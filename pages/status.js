(function () {
    'use strict';

    /* ===== Constants ===== */
    const PROM_URL = 'https://prometheus.gdutnic.com/api/v1';
    const PROM_K8S_URL = 'https://prometheus-k8s.gdutnic.com/api/v1';
    const HARBOR_JOB = 'job="harbor",namespace="gdut-mirrors"';
    const IPV4 = '202.116.132.67:9101';
    const IPV6 = '10.0.8.83:9101';
    const HOSTS = {
        [IPV4]: { name: 'IPv4 站点', short: 'IPv4', color: '#971943' },
        [IPV6]: { name: 'IPv6 站点', short: 'IPv6', color: '#3b82f6' }
    };
    const TIME_RANGES = {
        '1h':  { interval: '1m',  step: 15,  seconds: 3600 },
        '6h':  { interval: '5m',  step: 60,  seconds: 21600 },
        '24h': { interval: '10m', step: 120, seconds: 86400 }
    };
    const REFRESH_INTERVAL = 60;

    /* ===== State ===== */
    const state = { range: '1h', site: 'both', promOK: true, activeTab: 'mirrors' };
    const charts = {};   // id -> echarts instance
    const chartOpts = {}; // id -> last option (for re-theme)
    const chartFirstLoad = new Set(); // ids that haven't been rendered yet

    /* ===== Formatters ===== */
    function fmtBytes(b) {
        b = Number(b);
        if (!isFinite(b) || b < 0) return '-';
        const u = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
        let i = 0;
        while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
        return b.toFixed(i === 0 ? 0 : 2) + ' ' + u[i];
    }
    function fmtBps(b) {
        b = Number(b);
        if (!isFinite(b) || b < 0) return '-';
        const u = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps'];
        let i = 0;
        while (b >= 1000 && i < u.length - 1) { b /= 1000; i++; }
        return b.toFixed(2) + ' ' + u[i];
    }
    function fmtPct(p) {
        p = Number(p);
        if (!isFinite(p)) return '-';
        return p.toFixed(1) + '%';
    }
    function fmtUptime(days) {
        days = Number(days);
        if (!isFinite(days) || days < 0) return '-';
        const d = Math.floor(days);
        const h = Math.round((days - d) * 24);
        return d + '天' + h + '时';
    }
    function pctClass(p) {
        p = Number(p);
        if (!isFinite(p)) return '';
        if (p >= 85) return 'pct-crit';
        if (p >= 65) return 'pct-warn';
        return 'pct-good';
    }
    function healthColor(p) {
        p = Number(p);
        if (p >= 85) return '#ef4444';
        if (p >= 65) return '#f59e0b';
        return '#10b981';
    }
    function usageGradientColor(p) {
        p = Math.max(0, Math.min(100, Number(p)));
        var stops = [
            { v: 0,   r: 16,  g: 185, b: 129 },
            { v: 50,  r: 245, g: 158, b: 11  },
            { v: 70,  r: 249, g: 115, b: 22  },
            { v: 85,  r: 239, g: 68,  b: 68  },
            { v: 100, r: 239, g: 68,  b: 68  }
        ];
        for (var i = 0; i < stops.length - 1; i++) {
            if (p >= stops[i].v && p <= stops[i + 1].v) {
                var t = (p - stops[i].v) / (stops[i + 1].v - stops[i].v);
                var r = Math.round(stops[i].r + (stops[i + 1].r - stops[i].r) * t);
                var g = Math.round(stops[i].g + (stops[i + 1].g - stops[i].g) * t);
                var b = Math.round(stops[i].b + (stops[i + 1].b - stops[i].b) * t);
                return 'rgb(' + r + ',' + g + ',' + b + ')';
            }
        }
        return 'rgb(239,68,68)';
    }

    /* ===== CSS var helper ===== */
    function cssVar(name) {
        return getComputedStyle(document.body).getPropertyValue(name).trim();
    }

    /* ===== Prometheus query helpers ===== */
    async function promInstant(query) {
        const url = PROM_URL + '/query?query=' + encodeURIComponent(query);
        const res = await fetch(url);
        if (!res.ok) throw new Error('Prometheus HTTP ' + res.status);
        const json = await res.json();
        if (json.status !== 'success') throw new Error('Prometheus query failed: ' + (json.error || ''));
        return json.data.result;
    }
    async function promRange(query, start, end, step) {
        const url = PROM_URL + '/query_range?query=' + encodeURIComponent(query) +
                    '&start=' + start + '&end=' + end + '&step=' + step;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Prometheus HTTP ' + res.status);
        const json = await res.json();
        if (json.status !== 'success') throw new Error('Prometheus query failed: ' + (json.error || ''));
        return json.data.result;
    }
    function substitute(tpl, instance, interval) {
        let s = tpl;
        if (instance !== undefined) s = s.split('{INSTANCE}').join(instance);
        if (interval !== undefined) s = s.split('{INTERVAL}').join(interval);
        return s;
    }
    async function k8sInstant(query) {
        const url = PROM_K8S_URL + '/query?query=' + encodeURIComponent(query);
        const res = await fetch(url);
        if (!res.ok) throw new Error('k8s Prometheus HTTP ' + res.status);
        const json = await res.json();
        if (json.status !== 'success') throw new Error('k8s Prometheus query failed: ' + (json.error || ''));
        return json.data.result;
    }
    async function k8sRange(query, start, end, step) {
        const url = PROM_K8S_URL + '/query_range?query=' + encodeURIComponent(query) +
                    '&start=' + start + '&end=' + end + '&step=' + step;
        const res = await fetch(url);
        if (!res.ok) throw new Error('k8s Prometheus HTTP ' + res.status);
        const json = await res.json();
        if (json.status !== 'success') throw new Error('k8s Prometheus query failed: ' + (json.error || ''));
        return json.data.result;
    }

    /* ===== Instance selector from site choice ===== */
    function instanceSelector() {
        if (state.site === 'ipv4') return IPV4;
        if (state.site === 'ipv6') return IPV6;
        return IPV4 + '|' + IPV6;
    }
    function selectedInstances() {
        if (state.site === 'ipv4') return [IPV4];
        if (state.site === 'ipv6') return [IPV6];
        return [IPV4, IPV6];
    }

    /* ===== Chart helpers ===== */
    function getChart(id) {
        if (!charts[id]) {
            const el = document.getElementById(id);
            if (!el) return null;
            charts[id] = echarts.init(el);
        }
        return charts[id];
    }
    function themeColors() {
        return {
            text: cssVar('--color-text-muted'),
            border: cssVar('--color-border'),
            surface: cssVar('--color-surface'),
            textStrong: cssVar('--color-text')
        };
    }
    function baseTooltip() {
        const t = themeColors();
        return {
            trigger: 'axis',
            backgroundColor: t.surface,
            borderColor: t.border,
            textStyle: { color: t.textStrong },
            borderWidth: 1
        };
    }
    function baseAxis(extra) {
        const t = themeColors();
        return Object.assign({
            axisLine: { lineStyle: { color: t.border } },
            axisLabel: { color: t.text },
            splitLine: { lineStyle: { color: t.border, type: 'dashed' } }
        }, extra || {});
    }
    function timeXAxis() {
        return baseAxis({ type: 'time' });
    }
    // Tooltip formatter for dual-axis aggregate charts: '%' series get pct, others bytes or plain.
    function aggTooltipFormatter(isBytes) {
        return function (params) {
            const tc = themeColors();
            let html = '<div style="color:' + tc.textStrong + ';margin-bottom:4px;font-weight:600;">' +
                new Date(params[0].value[0]).toLocaleString() + '</div>';
            params.forEach(function (p) {
                const v = p.value[1];
                let s;
                if (p.seriesName === '使用率' || p.seriesName === '平均CPU%') s = fmtPct(v);
                else if (isBytes) s = fmtBytes(v);
                else s = isFinite(v) ? v.toFixed(2) : '-';
                html += '<div style="color:' + tc.text + ';">' + p.marker + ' ' + p.seriesName + ': ' + s + '</div>';
            });
            return html;
        };
    }
    function setChart(id, option) {
        const c = getChart(id);
        if (!c) return;
        chartOpts[id] = option;
        c.setOption(option, false);
        const wrap = document.getElementById('wrap-' + id.replace('chart-', ''));
        if (wrap) wrap.classList.add('loaded');
    }
    function showChartEmpty(id, msg) {
        const wrap = document.getElementById('wrap-' + id.replace('chart-', ''));
        if (!wrap) return;
        wrap.classList.remove('loaded');
        const el = wrap.querySelector('.chart-loading');
        if (el) { el.textContent = msg; el.classList.add('static'); }
    }
    function showChartLoading(id) {
        const wrap = document.getElementById('wrap-' + id.replace('chart-', ''));
        if (!wrap) return;
        wrap.classList.remove('loaded');
        const el = wrap.querySelector('.chart-loading');
        if (el) { el.textContent = '加载中…'; el.classList.remove('static'); }
    }
    function renderChart(id, option) {
        if (chartFirstLoad.has(id)) {
            chartFirstLoad.delete(id);
            var island = document.getElementById(id) && document.getElementById(id).closest('.island');
            if (island) {
                var obs = new IntersectionObserver(function (entries) {
                    if (entries[0].isIntersecting) {
                        obs.disconnect();
                        setTimeout(function () { setChart(id, option); }, 700);
                    }
                }, { threshold: 0.15 });
                obs.observe(island);
                return;
            }
        }
        if (!option.animationDuration) showChartLoading(id);
        setChart(id, option);
    }
    function matrixToSeries(result, nameFn, colorFn, yFmt) {
        return result.map(function (item) {
            const inst = item.metric.instance;
            const host = HOSTS[inst];
            return {
                name: nameFn(item, host),
                type: 'line',
                showSymbol: false,
                smooth: true,
                lineStyle: { width: 2 },
                itemStyle: { color: colorFn(item, host) },
                data: item.values.map(function (v) { return [v[0] * 1000, parseFloat(v[1])]; }),
                yAxisIndex: 0
            };
        });
    }

    /* ===== Skeleton helpers for tables ===== */
    function tableSkeleton(tbodyId, cols) {
        const tb = document.getElementById(tbodyId);
        if (!tb) return;
        let html = '';
        for (let r = 0; r < 2; r++) {
            html += '<tr>';
            for (let c = 0; c < cols; c++) {
                html += '<td><div style="height:14px;background:var(--color-border);border-radius:4px;animation:pulse 1.5s infinite;"></div></td>';
            }
            html += '</tr>';
        }
        tb.innerHTML = html;
    }
    function tableEmpty(tbodyId, msg, cols) {
        const tb = document.getElementById(tbodyId);
        if (!tb) return;
        tb.innerHTML = '<tr><td colspan="' + cols + '" style="text-align:center;color:var(--color-text-muted);padding:var(--spacing-lg);">' + msg + '</td></tr>';
    }

    /* ===== Panel 1: Overview cards (always both hosts) ===== */
    async function loadOverview() {
        const queries = [
            { key: 'up4', q: 'up{instance="' + IPV4 + '"}' },
            { key: 'cpu4', q: '(1 - avg(irate(node_cpu_seconds_total{instance="' + IPV4 + '",mode="idle"}[1m])) by (instance)) * 100' },
            { key: 'mem4', q: '(1 - (node_memory_MemAvailable_bytes{instance="' + IPV4 + '"} / node_memory_MemTotal_bytes{instance="' + IPV4 + '"})) * 100' },
            { key: 'up6', q: 'up{instance="' + IPV6 + '"}' },
            { key: 'cpu6', q: '(1 - avg(irate(node_cpu_seconds_total{instance="' + IPV6 + '",mode="idle"}[1m])) by (instance)) * 100' },
            { key: 'mem6', q: '(1 - (node_memory_MemAvailable_bytes{instance="' + IPV6 + '"} / node_memory_MemTotal_bytes{instance="' + IPV6 + '"})) * 100' }
        ];
        const results = await Promise.all(queries.map(function (q) { return promInstant(q.q).catch(function () { return []; }); }));
        const map = {};
        queries.forEach(function (q, i) { map[q.key] = results[i]; });

        function val(arr) { return arr && arr[0] ? parseFloat(arr[0].value[1]) : NaN; }

        // IPv4 status
        const up4 = val(map.up4);
        const el4s = document.getElementById('ov-ipv4-status');
        if (isFinite(up4)) {
            el4s.textContent = up4 === 1 ? '在线' : '离线';
            el4s.className = 'stat-value ' + (up4 === 1 ? 'ok' : 'err');
        } else { el4s.textContent = '--'; el4s.className = 'stat-value'; }

        const cpu4 = val(map.cpu4);
        document.getElementById('ov-ipv4-cpu').textContent = isFinite(cpu4) ? fmtPct(cpu4) : '--';
        document.getElementById('ov-ipv4-cpu').className = 'stat-value ' + (up4 === 1 ? '' : 'err');
        document.getElementById('ov-ipv4-cpu-sub').textContent = (up4 === 1 && isFinite(cpu4)) ? pctClass(cpu4).replace('pct-', '') : '';

        const mem4 = val(map.mem4);
        document.getElementById('ov-ipv4-mem').textContent = isFinite(mem4) ? fmtPct(mem4) : '--';
        document.getElementById('ov-ipv4-mem').className = 'stat-value ' + (up4 === 1 ? '' : 'err');
        document.getElementById('ov-ipv4-mem-sub').textContent = (up4 === 1 && isFinite(mem4)) ? pctClass(mem4).replace('pct-', '') : '';

        // IPv6 status
        const up6 = val(map.up6);
        const el6s = document.getElementById('ov-ipv6-status');
        if (isFinite(up6)) {
            el6s.textContent = up6 === 1 ? '在线' : '离线';
            el6s.className = 'stat-value ' + (up6 === 1 ? 'ok' : 'err');
        } else { el6s.textContent = '--'; el6s.className = 'stat-value'; }

        const cpu6 = val(map.cpu6);
        document.getElementById('ov-ipv6-cpu').textContent = isFinite(cpu6) ? fmtPct(cpu6) : '--';
        document.getElementById('ov-ipv6-cpu').className = 'stat-value ' + (up6 === 1 ? '' : 'err');
        document.getElementById('ov-ipv6-cpu-sub').textContent = (up6 === 1 && isFinite(cpu6)) ? pctClass(cpu6).replace('pct-', '') : '';

        const mem6 = val(map.mem6);
        document.getElementById('ov-ipv6-mem').textContent = isFinite(mem6) ? fmtPct(mem6) : '--';
        document.getElementById('ov-ipv6-mem').className = 'stat-value ' + (up6 === 1 ? '' : 'err');
        document.getElementById('ov-ipv6-mem-sub').textContent = (up6 === 1 && isFinite(mem6)) ? pctClass(mem6).replace('pct-', '') : '';
    }

    /* ===== Overview sparklines (background area charts) ===== */
    function hexToRgba(hex, alpha) {
        var r = parseInt(hex.slice(1, 3), 16);
        var g = parseInt(hex.slice(3, 5), 16);
        var b = parseInt(hex.slice(5, 7), 16);
        return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
    }
    function renderSpark(id, data, color) {
        var c = getChart(id);
        if (!c) return;
        if (!data || !data.length) { c.clear(); delete chartOpts[id]; return; }
        setChart(id, {
            backgroundColor: 'transparent',
            animation: true,
            animationDuration: 800,
            animationDurationUpdate: 800,
            animationEasing: 'cubicOut',
            grid: { left: 0, right: 0, top: 2, bottom: 0 },
            xAxis: { type: 'time', show: false },
            yAxis: { type: 'value', show: false, scale: true },
            series: [{
                type: 'line',
                showSymbol: false,
                smooth: true,
                data: data,
                lineStyle: { width: 1.5, color: color },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: hexToRgba(color, 0.35) },
                        { offset: 1, color: hexToRgba(color, 0) }
                    ])
                }
            }]
        });
    }
    async function loadOverviewSparks() {
        var iv = TIME_RANGES[state.range].interval;
        var step = TIME_RANGES[state.range].step;
        var end = Math.floor(Date.now() / 1000);
        var start = end - TIME_RANGES[state.range].seconds;
        var instBoth = IPV4 + '|' + IPV6;
        var qCpu = '(1 - avg(irate(node_cpu_seconds_total{instance=~"' + instBoth + '",mode="idle"}[' + iv + '])) by (instance)) * 100';
        var qMem = '(1 - (node_memory_MemAvailable_bytes{instance=~"' + instBoth + '"} / node_memory_MemTotal_bytes{instance=~"' + instBoth + '"})) * 100';
        var results = await Promise.all([
            promRange(qCpu, start, end, step).catch(function () { return []; }),
            promRange(qMem, start, end, step).catch(function () { return []; })
        ]);
        function toMap(res) {
            var m = {};
            res.forEach(function (item) {
                m[item.metric.instance] = item.values.map(function (v) { return [v[0] * 1000, parseFloat(v[1])]; });
            });
            return m;
        }
        var cpuMap = toMap(results[0]);
        var memMap = toMap(results[1]);
        renderSpark('spark-ipv4-cpu', cpuMap[IPV4], HOSTS[IPV4].color);
        renderSpark('spark-ipv4-mem', memMap[IPV4], HOSTS[IPV4].color);
        renderSpark('spark-ipv6-cpu', cpuMap[IPV6], HOSTS[IPV6].color);
        renderSpark('spark-ipv6-mem', memMap[IPV6], HOSTS[IPV6].color);
    }

    /* ===== Panel 2: Resource overview table ===== */
    async function loadResourceTable() {
        const inst = instanceSelector();
        const iv = TIME_RANGES[state.range].interval;
        tableSkeleton('resource-tbody', 13);
        const T = {
            uptime: 'sum(time() - node_boot_time_seconds{instance=~"{INSTANCE}"}) by (instance)/86400',
            memtotal: 'node_memory_MemTotal_bytes{instance=~"{INSTANCE}"} - 0',
            cpucount: "count(node_cpu_seconds_total{instance=~\"{INSTANCE}\",mode='system'}) by (instance)",
            load5: 'node_load5{instance=~"{INSTANCE}"}',
            cpuusage: '(1 - avg(irate(node_cpu_seconds_total{instance=~"{INSTANCE}",mode="idle"}[{INTERVAL}])) by (instance)) * 100',
            memusage: '(1 - (node_memory_MemAvailable_bytes{instance=~"{INSTANCE}"} / node_memory_MemTotal_bytes{instance=~"{INSTANCE}"}))* 100',
            diskusage: 'max((node_filesystem_size_bytes{instance=~"{INSTANCE}",fstype=~"ext.?|xfs",mountpoint=~"/|/home"}-node_filesystem_free_bytes{instance=~"{INSTANCE}",fstype=~"ext.?|xfs",mountpoint=~"/|/home"}) *100/(node_filesystem_avail_bytes{instance=~"{INSTANCE}",fstype=~"ext.?|xfs",mountpoint=~"/|/home"}+(node_filesystem_size_bytes{instance=~"{INSTANCE}",fstype=~"ext.?|xfs",mountpoint=~"/|/home"}-node_filesystem_free_bytes{instance=~"{INSTANCE}",fstype=~"ext.?|xfs",mountpoint=~"/|/home"})))by(instance)',
            diskread: 'max(irate(node_disk_read_bytes_total{instance=~"{INSTANCE}"}[{INTERVAL}])) by (instance)',
            diskwrite: 'max(irate(node_disk_written_bytes_total{instance=~"{INSTANCE}"}[{INTERVAL}])) by (instance)',
            netrx: 'max(irate(node_network_receive_bytes_total{instance=~"{INSTANCE}",device!~"lo|veth.*|wg.*|docker.*|cni.*|br.*|kube.*"}[{INTERVAL}])*8) by (instance)',
            nettx: 'max(irate(node_network_transmit_bytes_total{instance=~"{INSTANCE}",device!~"lo|veth.*|wg.*|docker.*|cni.*|br.*|kube.*"}[{INTERVAL}])*8) by (instance)'
        };
        const keys = Object.keys(T);
        const results = await Promise.all(keys.map(function (k) {
            return promInstant(substitute(T[k], inst, iv)).catch(function () { return []; });
        }));
        const data = {};
        keys.forEach(function (k, i) {
            const m = {};
            results[i].forEach(function (r) { m[r.metric.instance] = parseFloat(r.value[1]); });
            data[k] = m;
        });
        const instances = selectedInstances();
        let html = '';
        let any = false;
        instances.forEach(function (inst2) {
            const host = HOSTS[inst2];
            if (!host) return;
            any = true;
            const cpu = data.cpuusage[inst2];
            const mem = data.memusage[inst2];
            const disk = data.diskusage[inst2];
            const health = (isFinite(cpu) ? cpu : 0) * 0.5 + (isFinite(mem) ? mem : 0) * 0.3 + (isFinite(disk) ? disk : 0) * 0.2;
            html += '<tr>'
                + '<td class="col-site">' + host.name + '</td>'
                + '<td>' + fmtUptime(data.uptime[inst2]) + '</td>'
                + '<td>' + (isFinite(data.cpucount[inst2]) ? Math.round(data.cpucount[inst2]) : '-') + '</td>'
                + '<td>' + fmtBytes(data.memtotal[inst2]) + '</td>'
                + '<td class="pct-tag ' + pctClass(cpu) + '">' + fmtPct(cpu) + '</td>'
                + '<td class="pct-tag ' + pctClass(mem) + '">' + fmtPct(mem) + '</td>'
                + '<td class="pct-tag ' + pctClass(disk) + '">' + fmtPct(disk) + '</td>'
                + '<td>' + (isFinite(data.load5[inst2]) ? data.load5[inst2].toFixed(2) : '-') + '</td>'
                + '<td>' + (isFinite(data.diskread[inst2]) ? fmtBytes(data.diskread[inst2]) + '/s' : '-') + '</td>'
                + '<td>' + (isFinite(data.diskwrite[inst2]) ? fmtBytes(data.diskwrite[inst2]) + '/s' : '-') + '</td>'
                + '<td>' + fmtBps(data.netrx[inst2]) + '</td>'
                + '<td>' + fmtBps(data.nettx[inst2]) + '</td>'
                + '<td><span class="health-bar"><span class="health-track"><span class="health-fill" style="width:' + health.toFixed(1) + '%;background:' + healthColor(health) + ';"></span></span><span class="pct-tag ' + pctClass(health) + '">' + health.toFixed(1) + '</span></span></td>'
                + '</tr>';
        });
        if (!any) { tableEmpty('resource-tbody', '暂无数据', 13); return; }
        document.getElementById('resource-tbody').innerHTML = html;
    }

    /* ===== Panel 3: 7-day P99 table ===== */
    async function loadP99Table() {
        const inst = instanceSelector();
        tableSkeleton('p99-tbody', 3);
        const T = {
            cpu: 'quantile_over_time(0.99, cpu:usage:rate1m{instance=~"{INSTANCE}"}[7d:1h])',
            mem: 'quantile_over_time(0.99, mem:usage:rate1m{instance=~"{INSTANCE}"}[7d:1h])'
        };
        const results = await Promise.all([
            promInstant(substitute(T.cpu, inst)).catch(function () { return []; }),
            promInstant(substitute(T.mem, inst)).catch(function () { return []; })
        ]);
        const cpuMap = {}, memMap = {};
        results[0].forEach(function (r) { cpuMap[r.metric.instance] = parseFloat(r.value[1]); });
        results[1].forEach(function (r) { memMap[r.metric.instance] = parseFloat(r.value[1]); });
        const instances = selectedInstances();
        let html = '', any = false;
        instances.forEach(function (inst2) {
            const host = HOSTS[inst2];
            if (!host) return;
            if (!isFinite(cpuMap[inst2]) && !isFinite(memMap[inst2])) return;
            any = true;
            const cpu = cpuMap[inst2], mem = memMap[inst2];
            html += '<tr>'
                + '<td class="col-site">' + host.name + '</td>'
                + '<td class="pct-tag ' + pctClass(cpu) + '">' + (isFinite(cpu) ? fmtPct(cpu) : '-') + '</td>'
                + '<td class="pct-tag ' + pctClass(mem) + '">' + (isFinite(mem) ? fmtPct(mem) : '-') + '</td>'
                + '</tr>';
        });
        if (!any) { tableEmpty('p99-tbody', '暂无数据（recording rules 可能未配置）', 3); return; }
        document.getElementById('p99-tbody').innerHTML = html;
    }

    /* ===== Panel 4: Partition table ===== */
    async function loadPartitionTable() {
        const inst = instanceSelector();
        tableSkeleton('partition-tbody', 5);
        const T = {
            total: 'node_filesystem_size_bytes{instance=~"{INSTANCE}",fstype=~"ext.*|xfs",mountpoint=~"/|/home"}-0',
            avail: 'node_filesystem_avail_bytes{instance=~"{INSTANCE}",fstype=~"ext.*|xfs",mountpoint=~"/|/home"}-0',
            usage: '(node_filesystem_size_bytes{instance=~"{INSTANCE}",fstype=~"ext.*|xfs",mountpoint=~"/|/home"}-node_filesystem_free_bytes{instance=~"{INSTANCE}",fstype=~"ext.*|xfs",mountpoint=~"/|/home"}) *100/(node_filesystem_avail_bytes{instance=~"{INSTANCE}",fstype=~"ext.*|xfs",mountpoint=~"/|/home"}+(node_filesystem_size_bytes{instance=~"{INSTANCE}",fstype=~"ext.*|xfs",mountpoint=~"/|/home"}-node_filesystem_free_bytes{instance=~"{INSTANCE}",fstype=~"ext.*|xfs",mountpoint=~"/|/home"}))'
        };
        const results = await Promise.all([
            promInstant(substitute(T.total, inst)).catch(function () { return []; }),
            promInstant(substitute(T.avail, inst)).catch(function () { return []; }),
            promInstant(substitute(T.usage, inst)).catch(function () { return []; })
        ]);
        // Build map keyed by instance|mountpoint
        const rows = {};
        results[0].forEach(function (r) {
            const k = r.metric.instance + '|' + r.metric.mountpoint;
            rows[k] = { instance: r.metric.instance, mountpoint: r.metric.mountpoint, total: parseFloat(r.value[1]) };
        });
        results[1].forEach(function (r) {
            const k = r.metric.instance + '|' + r.metric.mountpoint;
            if (rows[k]) rows[k].avail = parseFloat(r.value[1]);
        });
        results[2].forEach(function (r) {
            const k = r.metric.instance + '|' + r.metric.mountpoint;
            if (rows[k]) rows[k].usage = parseFloat(r.value[1]);
        });
        const keys = Object.keys(rows);
        if (!keys.length) { tableEmpty('partition-tbody', '暂无数据', 5); return; }
        // Order by instance order then mountpoint
        const insts = selectedInstances();
        let html = '';
        insts.forEach(function (inst2) {
            keys.filter(function (k) { return rows[k].instance === inst2; })
                .sort(function (a, b) { return rows[a].mountpoint.localeCompare(rows[b].mountpoint); })
                .forEach(function (k) {
                    const r = rows[k];
                    const host = HOSTS[r.instance];
                    if (!host) return;
                    const u = isFinite(r.usage) ? r.usage : NaN;
                    var uClamped = Math.max(0, Math.min(100, isFinite(u) ? u : 0));
                    var barColor = usageGradientColor(uClamped);
                    html += '<tr class="partition-row" data-bar-w="' + uClamped.toFixed(1) + '" data-bar-c="' + barColor + '">'
                        + '<td class="col-site">' + host.name + '</td>'
                        + '<td>' + (r.mountpoint || '-') + '</td>'
                        + '<td>' + fmtBytes(r.total) + '</td>'
                        + '<td>' + fmtBytes(r.avail) + '</td>'
                        + '<td class="pct-tag ' + pctClass(u) + '">' + fmtPct(u) + '</td>'
                        + '</tr>';
                });
        });
        document.getElementById('partition-tbody').innerHTML = html;
        // Animate progress bars from left to right, but only after island is visible and fadeIn complete
        var island = document.getElementById('partition-tbody').closest('.island');
        var barRows = document.querySelectorAll('#partition-tbody .partition-row');
        // Set initial 0% state immediately
        barRows.forEach(function (tr) {
            var color = tr.dataset.barC || 'transparent';
            tr.style.background = 'linear-gradient(90deg, ' + color + ' 0%, transparent 0%)';
        });

        function runBarAnimation() {
            barRows.forEach(function (tr, idx) {
                var targetW = parseFloat(tr.dataset.barW) || 0;
                var color = tr.dataset.barC || 'transparent';
                setTimeout(function () {
                    var startTime = null;
                    function step(ts) {
                        if (!startTime) startTime = ts;
                        var progress = Math.min((ts - startTime) / 1200, 1);
                        var eased = 1 - Math.pow(1 - progress, 3);
                        var curW = targetW * eased;
                        tr.style.background = 'linear-gradient(90deg, ' + color + ' ' + curW.toFixed(1) + '%, transparent ' + curW.toFixed(1) + '%)';
                        if (progress < 1) requestAnimationFrame(step);
                    }
                    requestAnimationFrame(step);
                }, idx * 150);
            });
        }

        if (island) {
            var visObs = new IntersectionObserver(function (entries) {
                if (entries[0].isIntersecting) {
                    visObs.disconnect();
                    // Wait for island fadeIn animation to finish before starting bar animation
                    setTimeout(runBarAnimation, 700);
                }
            }, { threshold: 0.15 });
            visObs.observe(island);
        }
    }

    /* ===== Panel 5: CPU timeseries ===== */
    async function loadCpuChart() {
        showChartLoading('chart-cpu');
        const inst = instanceSelector();
        const iv = TIME_RANGES[state.range].interval;
        const step = TIME_RANGES[state.range].step;
        const end = Math.floor(Date.now() / 1000);
        const start = end - TIME_RANGES[state.range].seconds;
        const q = '(1 - avg(irate(node_cpu_seconds_total{instance=~"' + inst + '",mode="idle"}[' + iv + '])) by (instance))*100';
        try {
            const result = await promRange(q, start, end, step);
            if (!result.length) { showChartEmpty('chart-cpu', '暂无数据'); return; }
            const series = matrixToSeries(result,
                function (item, host) { return host ? host.short : item.metric.instance; },
                function (item, host) { return host ? host.color : '#999'; });
            renderChart('chart-cpu', {
                backgroundColor: 'transparent',
                tooltip: Object.assign(baseTooltip(), { valueFormatter: function (v) { return fmtPct(v); } }),
                legend: { top: 0, textStyle: { color: themeColors().text } },
                grid: { left: 50, right: 20, top: 36, bottom: 30 },
                xAxis: timeXAxis(),
                yAxis: baseAxis({ type: 'value', axisLabel: { color: themeColors().text, formatter: '{value}%' }, max: 100 }),
                series: series
            });
        } catch (e) { showChartEmpty('chart-cpu', '加载失败'); }
    }

    /* ===== Panel 6: Memory timeseries ===== */
    async function loadMemChart() {
        showChartLoading('chart-mem');
        const inst = instanceSelector();
        const step = TIME_RANGES[state.range].step;
        const end = Math.floor(Date.now() / 1000);
        const start = end - TIME_RANGES[state.range].seconds;
        const qUsed = 'node_memory_MemTotal_bytes{instance=~"' + inst + '"} - node_memory_MemAvailable_bytes{instance=~"' + inst + '"}';
        const qTotal = 'node_memory_MemTotal_bytes{instance=~"' + inst + '"}';
        try {
            const results = await Promise.all([
                promRange(qUsed, start, end, step).catch(function () { return []; }),
                promRange(qTotal, start, end, step).catch(function () { return []; })
            ]);
            const usedSeries = matrixToSeries(results[0],
                function (item, host) { return host ? host.short + ' 已用' : item.metric.instance; },
                function (item, host) { return host ? host.color : '#999'; });
            const totalSeries = results[1].map(function (item) {
                const host = HOSTS[item.metric.instance];
                return {
                    name: host ? host.short + ' 总量' : item.metric.instance,
                    type: 'line', showSymbol: false, smooth: true,
                    lineStyle: { width: 1, type: 'dashed' },
                    itemStyle: { color: host ? host.color : '#999' },
                    data: item.values.map(function (v) { return [v[0] * 1000, parseFloat(v[1])]; })
                };
            });
            if (!usedSeries.length && !totalSeries.length) { showChartEmpty('chart-mem', '暂无数据'); return; }
            renderChart('chart-mem', {
                backgroundColor: 'transparent',
                tooltip: Object.assign(baseTooltip(), { valueFormatter: function (v) { return fmtBytes(v); } }),
                legend: { top: 0, textStyle: { color: themeColors().text } },
                grid: { left: 60, right: 20, top: 36, bottom: 30 },
                xAxis: timeXAxis(),
                yAxis: baseAxis({ type: 'value', axisLabel: { color: themeColors().text, formatter: function (v) { return fmtBytes(v); } } }),
                series: usedSeries.concat(totalSeries)
            });
        } catch (e) { showChartEmpty('chart-mem', '加载失败'); }
    }

    /* ===== Panel 7: Disk timeseries ===== */
    async function loadDiskChart() {
        showChartLoading('chart-disk');
        const inst = instanceSelector();
        const step = TIME_RANGES[state.range].step;
        const end = Math.floor(Date.now() / 1000);
        const start = end - TIME_RANGES[state.range].seconds;
        const q = '(node_filesystem_size_bytes{instance=~"' + inst + '",fstype=~"ext.*|xfs",mountpoint=~"/|/home"}-node_filesystem_free_bytes{instance=~"' + inst + '",fstype=~"ext.*|xfs",mountpoint=~"/|/home"}) *100/(node_filesystem_avail_bytes{instance=~"' + inst + '",fstype=~"ext.*|xfs",mountpoint=~"/|/home"}+(node_filesystem_size_bytes{instance=~"' + inst + '",fstype=~"ext.*|xfs",mountpoint=~"/|/home"}-node_filesystem_free_bytes{instance=~"' + inst + '",fstype=~"ext.*|xfs",mountpoint=~"/|/home"}))';
        try {
            const result = await promRange(q, start, end, step);
            if (!result.length) { showChartEmpty('chart-disk', '暂无数据'); return; }
            const series = result.map(function (item) {
                const host = HOSTS[item.metric.instance];
                const mp = item.metric.mountpoint || '';
                return {
                    name: (host ? host.short : item.metric.instance) + ' ' + mp,
                    type: 'line', showSymbol: false, smooth: true,
                    lineStyle: { width: 2 },
                    itemStyle: { color: host ? host.color : '#999' },
                    data: item.values.map(function (v) { return [v[0] * 1000, parseFloat(v[1])]; })
                };
            });
            renderChart('chart-disk', {
                backgroundColor: 'transparent',
                tooltip: Object.assign(baseTooltip(), { valueFormatter: function (v) { return fmtPct(v); } }),
                legend: { top: 0, textStyle: { color: themeColors().text } },
                grid: { left: 50, right: 20, top: 36, bottom: 30 },
                xAxis: timeXAxis(),
                yAxis: baseAxis({ type: 'value', axisLabel: { color: themeColors().text, formatter: '{value}%' }, max: 100 }),
                series: series
            });
        } catch (e) { showChartEmpty('chart-disk', '加载失败'); }
    }

    /* ===== Panel 8: Load timeseries ===== */
    async function loadLoadChart() {
        showChartLoading('chart-load');
        const inst = instanceSelector();
        const step = TIME_RANGES[state.range].step;
        const end = Math.floor(Date.now() / 1000);
        const start = end - TIME_RANGES[state.range].seconds;
        const q = 'node_load5{instance=~"' + inst + '"}';
        try {
            const result = await promRange(q, start, end, step);
            if (!result.length) { showChartEmpty('chart-load', '暂无数据'); return; }
            const series = matrixToSeries(result,
                function (item, host) { return host ? host.short : item.metric.instance; },
                function (item, host) { return host ? host.color : '#999'; });
            renderChart('chart-load', {
                backgroundColor: 'transparent',
                tooltip: baseTooltip(),
                legend: { top: 0, textStyle: { color: themeColors().text } },
                grid: { left: 50, right: 20, top: 36, bottom: 30 },
                xAxis: timeXAxis(),
                yAxis: baseAxis({ type: 'value' }),
                series: series
            });
        } catch (e) { showChartEmpty('chart-load', '加载失败'); }
    }

    /* ===== Panel 9: Network bandwidth ===== */
    async function loadNetChart() {
        showChartLoading('chart-net');
        const inst = instanceSelector();
        const iv = TIME_RANGES[state.range].interval;
        const step = TIME_RANGES[state.range].step;
        const end = Math.floor(Date.now() / 1000);
        const start = end - TIME_RANGES[state.range].seconds;
        const devFilter = 'device!~"lo|veth.*|wg.*|docker.*|cni.*|br.*|kube.*"';
        const qRx = 'sum(irate(node_network_receive_bytes_total{instance=~"' + inst + '",' + devFilter + '}[' + iv + '])*8) by (instance)';
        const qTx = 'sum(irate(node_network_transmit_bytes_total{instance=~"' + inst + '",' + devFilter + '}[' + iv + '])*8) by (instance)';
        try {
            const results = await Promise.all([
                promRange(qRx, start, end, step).catch(function () { return []; }),
                promRange(qTx, start, end, step).catch(function () { return []; })
            ]);
            const rxSeries = matrixToSeries(results[0],
                function (item, host) { return host ? host.short + ' 接收' : item.metric.instance; },
                function (item, host) { return host ? host.color : '#999'; });
            const txSeries = matrixToSeries(results[1],
                function (item, host) { return host ? host.short + ' 发送' : item.metric.instance; },
                function (item, host) { return host ? host.color : '#999'; });
            // Distinguish tx by dashed line
            txSeries.forEach(function (s) { s.lineStyle = { width: 2, type: 'dashed' }; });
            if (!rxSeries.length && !txSeries.length) { showChartEmpty('chart-net', '暂无数据'); return; }
            renderChart('chart-net', {
                backgroundColor: 'transparent',
                tooltip: Object.assign(baseTooltip(), { valueFormatter: function (v) { return fmtBps(v); } }),
                legend: { top: 0, textStyle: { color: themeColors().text } },
                grid: { left: 60, right: 20, top: 36, bottom: 30 },
                xAxis: timeXAxis(),
                yAxis: baseAxis({ type: 'value', axisLabel: { color: themeColors().text, formatter: function (v) { return fmtBps(v); } } }),
                series: rxSeries.concat(txSeries)
            });
        } catch (e) { showChartEmpty('chart-net', '加载失败'); }
    }

    /* ===== Panel 10: Bargauge ===== */
    async function loadBargauge() {
        if (chartFirstLoad.has('chart-bargauge')) showChartLoading('chart-bargauge');
        const inst = instanceSelector();
        const iv = TIME_RANGES[state.range].interval;
        const T = {
            cpu: '100 - (avg(irate(node_cpu_seconds_total{instance=~"' + inst + '",mode="idle"}[' + iv + '])) by (instance) * 100)',
            iowait: 'avg(irate(node_cpu_seconds_total{instance=~"' + inst + '",mode="iowait"}[' + iv + '])) by (instance) * 100',
            mem: '(1 - (node_memory_MemAvailable_bytes{instance=~"' + inst + '"} / node_memory_MemTotal_bytes{instance=~"' + inst + '"}))* 100',
            disk: '(node_filesystem_size_bytes{instance=~"' + inst + '",fstype=~"ext.*|xfs",mountpoint="/home"}-node_filesystem_free_bytes{instance=~"' + inst + '",fstype=~"ext.*|xfs",mountpoint="/home"})*100/(node_filesystem_avail_bytes{instance=~"' + inst + '",fstype=~"ext.*|xfs",mountpoint="/home"}+(node_filesystem_size_bytes{instance=~"' + inst + '",fstype=~"ext.*|xfs",mountpoint="/home"}-node_filesystem_free_bytes{instance=~"' + inst + '",fstype=~"ext.*|xfs",mountpoint="/home"}))',
            swap: '(1 - ((node_memory_SwapFree_bytes{instance=~"' + inst + '"} + 1)/ (node_memory_SwapTotal_bytes{instance=~"' + inst + '"} + 1))) * 100'
        };
        const keys = Object.keys(T);
        try {
            const results = await Promise.all(keys.map(function (k) { return promInstant(T[k]).catch(function () { return []; }); }));
            const cats = ['CPU', 'iowait', '内存', '磁盘', 'swap'];
            const insts = selectedInstances();
            const series = insts.map(function (inst2) {
                const host = HOSTS[inst2];
                const vals = keys.map(function (k, i) {
                    const arr = results[i];
                    const found = arr.find(function (r) { return r.metric.instance === inst2; });
                    return found ? parseFloat(found.value[1]) : 0;
                });
                return {
                    name: host ? host.name : inst2,
                    type: 'bar',
                    barMaxWidth: 24,
                    itemStyle: { color: host ? host.color : '#999', borderRadius: [0, 4, 4, 0] },
                    data: vals
                };
            });
            if (!series.length) { showChartEmpty('chart-bargauge', '暂无数据'); return; }
            renderChart('chart-bargauge', {
                backgroundColor: 'transparent',
                animationDuration: 1200,
                animationEasing: 'cubicOut',
                animationDelay: function (idx) { return idx * 150; },
                tooltip: Object.assign(baseTooltip(), { trigger: 'item', valueFormatter: function (v) { return fmtPct(v); } }),
                legend: { top: 0, textStyle: { color: themeColors().text } },
                grid: { left: 60, right: 20, top: 36, bottom: 30 },
                xAxis: baseAxis({ type: 'value', max: 100, axisLabel: { color: themeColors().text, formatter: '{value}%' } }),
                yAxis: baseAxis({ type: 'category', data: cats, splitLine: { show: false } }),
                series: series
            });
        } catch (e) { showChartEmpty('chart-bargauge', '加载失败'); }
    }

    /* ===== Panel 11: Aggregate total load + avg CPU ===== */
    async function loadAggLoad() {
        showChartLoading('chart-agg-load');
        const inst = instanceSelector();
        const iv = TIME_RANGES[state.range].interval;
        const step = TIME_RANGES[state.range].step;
        const end = Math.floor(Date.now() / 1000);
        const start = end - TIME_RANGES[state.range].seconds;
        const T = {
            load: 'sum(node_load5{instance=~"' + inst + '"})',
            cores: 'count(node_cpu_seconds_total{instance=~"' + inst + '",mode=\'system\'})',
            avgcpu: 'avg(1 - avg(irate(node_cpu_seconds_total{instance=~"' + inst + '",mode="idle"}[' + iv + '])) by (instance)) * 100'
        };
        try {
            const results = await Promise.all([
                promRange(T.load, start, end, step).catch(function () { return []; }),
                promRange(T.cores, start, end, step).catch(function () { return []; }),
                promRange(T.avgcpu, start, end, step).catch(function () { return []; })
            ]);
            const tc = themeColors();
            function toData(res) {
                if (!res[0] || !res[0].values) return [];
                return res[0].values.map(function (v) { return [v[0] * 1000, parseFloat(v[1])]; });
            }
            const series = [
                { name: '总负载', type: 'line', showSymbol: false, smooth: true, yAxisIndex: 0, itemStyle: { color: '#971943' }, lineStyle: { width: 2 }, data: toData(results[0]) },
                { name: 'CPU核数', type: 'line', showSymbol: false, smooth: true, yAxisIndex: 0, itemStyle: { color: '#8b5cf6' }, lineStyle: { width: 2, type: 'dashed' }, data: toData(results[1]) },
                { name: '平均CPU%', type: 'line', showSymbol: false, smooth: true, yAxisIndex: 1, itemStyle: { color: '#3b82f6' }, lineStyle: { width: 2 }, data: toData(results[2]) }
            ];
            if (!series[0].data.length && !series[2].data.length) { showChartEmpty('chart-agg-load', '暂无数据'); return; }
            renderChart('chart-agg-load', {
                backgroundColor: 'transparent',
                tooltip: Object.assign(baseTooltip(), { formatter: aggTooltipFormatter(false) }),
                legend: { top: 0, textStyle: { color: tc.text } },
                grid: { left: 60, right: 60, top: 36, bottom: 30 },
                xAxis: timeXAxis(),
                yAxis: [
                    baseAxis({ type: 'value', name: '负载/核数', nameTextStyle: { color: tc.text }, position: 'left' }),
                    baseAxis({ type: 'value', name: 'CPU%', max: 100, nameTextStyle: { color: tc.text }, position: 'right', axisLabel: { color: tc.text, formatter: '{value}%' } })
                ],
                series: series
            });
        } catch (e) { showChartEmpty('chart-agg-load', '加载失败'); }
    }

    /* ===== Panel 12: Total memory ===== */
    async function loadAggMem() {
        showChartLoading('chart-agg-mem');
        const inst = instanceSelector();
        const step = TIME_RANGES[state.range].step;
        const end = Math.floor(Date.now() / 1000);
        const start = end - TIME_RANGES[state.range].seconds;
        const qUsed = 'sum(node_memory_MemTotal_bytes{instance=~"' + inst + '"} - node_memory_MemAvailable_bytes{instance=~"' + inst + '"})';
        const qTotal = 'sum(node_memory_MemTotal_bytes{instance=~"' + inst + '"})';
        const qUsage = '(sum(node_memory_MemTotal_bytes{instance=~"' + inst + '"} - node_memory_MemAvailable_bytes{instance=~"' + inst + '"}) / sum(node_memory_MemTotal_bytes{instance=~"' + inst + '"}))*100';
        try {
            const results = await Promise.all([
                promRange(qUsed, start, end, step).catch(function () { return []; }),
                promRange(qTotal, start, end, step).catch(function () { return []; }),
                promRange(qUsage, start, end, step).catch(function () { return []; })
            ]);
            const tc = themeColors();
            function toData(res) {
                if (!res[0] || !res[0].values) return [];
                return res[0].values.map(function (v) { return [v[0] * 1000, parseFloat(v[1])]; });
            }
            const series = [
                { name: '已用', type: 'line', showSymbol: false, smooth: true, yAxisIndex: 0, itemStyle: { color: '#971943' }, lineStyle: { width: 2 }, data: toData(results[0]) },
                { name: '总量', type: 'line', showSymbol: false, smooth: true, yAxisIndex: 0, itemStyle: { color: '#8b5cf6' }, lineStyle: { width: 2, type: 'dashed' }, data: toData(results[1]) },
                { name: '使用率', type: 'line', showSymbol: false, smooth: true, yAxisIndex: 1, itemStyle: { color: '#3b82f6' }, lineStyle: { width: 2 }, data: toData(results[2]) }
            ];
            if (!series[0].data.length && !series[1].data.length) { showChartEmpty('chart-agg-mem', '暂无数据'); return; }
            renderChart('chart-agg-mem', {
                backgroundColor: 'transparent',
                tooltip: Object.assign(baseTooltip(), { formatter: aggTooltipFormatter(true) }),
                legend: { top: 0, textStyle: { color: tc.text } },
                grid: { left: 70, right: 50, top: 36, bottom: 30 },
                xAxis: timeXAxis(),
                yAxis: [
                    baseAxis({ type: 'value', name: '内存', nameTextStyle: { color: tc.text }, axisLabel: { color: tc.text, formatter: function (v) { return fmtBytes(v); } } }),
                    baseAxis({ type: 'value', name: '%', max: 100, nameTextStyle: { color: tc.text }, position: 'right', axisLabel: { color: tc.text, formatter: '{value}%' } })
                ],
                series: series
            });
        } catch (e) { showChartEmpty('chart-agg-mem', '加载失败'); }
    }

    /* ===== Panel 13: Total disk ===== */
    async function loadAggDisk() {
        showChartLoading('chart-agg-disk');
        const inst = instanceSelector();
        const step = TIME_RANGES[state.range].step;
        const end = Math.floor(Date.now() / 1000);
        const start = end - TIME_RANGES[state.range].seconds;
        const qUsed = 'sum(avg(node_filesystem_size_bytes{instance=~"' + inst + '",fstype=~"xfs|ext.*",mountpoint=~"/|/home"})by(device,instance)) - sum(avg(node_filesystem_free_bytes{instance=~"' + inst + '",fstype=~"xfs|ext.*",mountpoint=~"/|/home"})by(device,instance))';
        const qTotal = 'sum(avg(node_filesystem_size_bytes{instance=~"' + inst + '",fstype=~"xfs|ext.*",mountpoint=~"/|/home"})by(device,instance))';
        const qUsage = '(sum(avg(node_filesystem_size_bytes{instance=~"' + inst + '",fstype=~"xfs|ext.*",mountpoint=~"/|/home"})by(device,instance)) - sum(avg(node_filesystem_free_bytes{instance=~"' + inst + '",fstype=~"xfs|ext.*",mountpoint=~"/|/home"})by(device,instance))) / sum(avg(node_filesystem_size_bytes{instance=~"' + inst + '",fstype=~"xfs|ext.*",mountpoint=~"/|/home"})by(device,instance)) * 100';
        try {
            const results = await Promise.all([
                promRange(qUsed, start, end, step).catch(function () { return []; }),
                promRange(qTotal, start, end, step).catch(function () { return []; }),
                promRange(qUsage, start, end, step).catch(function () { return []; })
            ]);
            const tc = themeColors();
            function toData(res) {
                if (!res[0] || !res[0].values) return [];
                return res[0].values.map(function (v) { return [v[0] * 1000, parseFloat(v[1])]; });
            }
            const series = [
                { name: '已用', type: 'line', showSymbol: false, smooth: true, yAxisIndex: 0, itemStyle: { color: '#971943' }, lineStyle: { width: 2 }, data: toData(results[0]) },
                { name: '总量', type: 'line', showSymbol: false, smooth: true, yAxisIndex: 0, itemStyle: { color: '#8b5cf6' }, lineStyle: { width: 2, type: 'dashed' }, data: toData(results[1]) },
                { name: '使用率', type: 'line', showSymbol: false, smooth: true, yAxisIndex: 1, itemStyle: { color: '#3b82f6' }, lineStyle: { width: 2 }, data: toData(results[2]) }
            ];
            if (!series[0].data.length && !series[1].data.length) { showChartEmpty('chart-agg-disk', '暂无数据'); return; }
            renderChart('chart-agg-disk', {
                backgroundColor: 'transparent',
                tooltip: Object.assign(baseTooltip(), { formatter: aggTooltipFormatter(true) }),
                legend: { top: 0, textStyle: { color: tc.text } },
                grid: { left: 70, right: 50, top: 36, bottom: 30 },
                xAxis: timeXAxis(),
                yAxis: [
                    baseAxis({ type: 'value', name: '磁盘', nameTextStyle: { color: tc.text }, axisLabel: { color: tc.text, formatter: function (v) { return fmtBytes(v); } } }),
                    baseAxis({ type: 'value', name: '%', max: 100, nameTextStyle: { color: tc.text }, position: 'right', axisLabel: { color: tc.text, formatter: '{value}%' } })
                ],
                series: series
            });
        } catch (e) { showChartEmpty('chart-agg-disk', '加载失败'); }
    }

    /* ===== Harbor: Overview stat cards ===== */
    async function loadHarborOverview() {
        var sel = '{' + HARBOR_JOB + '}';
        var queries = [
            { key: 'up', q: 'harbor_up' + sel },
            { key: 'projects', q: 'harbor_statistics_total_project_amount' + sel },
            { key: 'repos', q: 'harbor_statistics_total_repo_amount' + sel },
            { key: 'storage', q: 'harbor_statistics_total_storage_consumption' + sel },
            { key: 'priv_proj', q: 'harbor_statistics_private_project_amount' + sel },
            { key: 'pub_proj', q: 'harbor_statistics_public_project_amount' + sel },
            { key: 'priv_repo', q: 'harbor_statistics_private_repo_amount' + sel },
            { key: 'pub_repo', q: 'harbor_statistics_public_repo_amount' + sel }
        ];
        var results = await Promise.all(queries.map(function (q) { return k8sInstant(q.q).catch(function () { return []; }); }));
        var map = {};
        queries.forEach(function (q, i) { map[q.key] = results[i]; });

        var upResults = map.up || [];
        var upCount = upResults.filter(function (r) { return r.value[1] === '1'; }).length;
        var totalComponents = upResults.length;
        var elHealth = document.getElementById('hb-health');
        if (totalComponents > 0) {
            elHealth.textContent = upCount + '/' + totalComponents;
            elHealth.className = 'stat-value ' + (upCount === totalComponents ? 'ok' : 'err');
        } else { elHealth.textContent = '--'; elHealth.className = 'stat-value'; }
        document.getElementById('hb-health-sub').textContent = totalComponents > 0 ? (upCount === totalComponents ? '全部在线' : (totalComponents - upCount) + ' 个离线') : '';

        function val(arr) { return arr && arr[0] ? parseFloat(arr[0].value[1]) : NaN; }
        var projects = val(map.projects);
        document.getElementById('hb-projects').textContent = isFinite(projects) ? String(projects) : '--';
        document.getElementById('hb-projects-sub').textContent = isFinite(projects) ? '私有 ' + (val(map.priv_proj) | 0) + ' · 公开 ' + (val(map.pub_proj) | 0) : '';

        var repos = val(map.repos);
        document.getElementById('hb-repos').textContent = isFinite(repos) ? String(repos) : '--';
        document.getElementById('hb-repos-sub').textContent = isFinite(repos) ? '私有 ' + (val(map.priv_repo) | 0) + ' · 公开 ' + (val(map.pub_repo) | 0) : '';

        var storage = val(map.storage);
        document.getElementById('hb-storage').textContent = isFinite(storage) ? fmtBytes(storage) : '--';
        document.getElementById('hb-storage-sub').textContent = '';
    }

    /* ===== Harbor: Project storage table ===== */
    async function loadHarborProjectTable() {
        tableSkeleton('harbor-project-tbody', 5);
        var sel = '{' + HARBOR_JOB + '}';
        var results = await Promise.all([
            k8sInstant('harbor_project_quota_usage_byte' + sel).catch(function () { return []; }),
            k8sInstant('harbor_project_quota_byte' + sel).catch(function () { return []; }),
            k8sInstant('harbor_artifact_pulled' + sel).catch(function () { return []; })
        ]);
        var usageMap = {}, quotaMap = {}, pullMap = {};
        results[0].forEach(function (r) { usageMap[r.metric.project_name] = parseFloat(r.value[1]); });
        results[1].forEach(function (r) { quotaMap[r.metric.project_name] = parseFloat(r.value[1]); });
        results[2].forEach(function (r) { pullMap[r.metric.project_name] = parseFloat(r.value[1]); });
        var projects = Object.keys(usageMap);
        if (!projects.length) { tableEmpty('harbor-project-tbody', '暂无数据', 5); return; }
        projects.sort(function (a, b) { return (usageMap[b] || 0) - (usageMap[a] || 0); });
        var html = '';
        projects.forEach(function (name) {
            var used = usageMap[name] || 0;
            var quota = quotaMap[name] || 0;
            var pulls = pullMap[name] || 0;
            var pct = quota > 0 ? (used / quota * 100) : 0;
            var uClamped = Math.max(0, Math.min(100, pct));
            var barColor = usageGradientColor(uClamped);
            html += '<tr class="partition-row" data-bar-w="' + uClamped.toFixed(1) + '" data-bar-c="' + barColor + '">'
                + '<td class="col-site">' + name + '</td>'
                + '<td>' + fmtBytes(used) + '</td>'
                + '<td>' + (quota > 0 ? fmtBytes(quota) : '-') + '</td>'
                + '<td class="pct-tag ' + pctClass(pct) + '">' + (quota > 0 ? fmtPct(pct) : '-') + '</td>'
                + '<td>' + (pulls > 0 ? String(pulls) : '-') + '</td>'
                + '</tr>';
        });
        document.getElementById('harbor-project-tbody').innerHTML = html;
        var barRows = document.querySelectorAll('#harbor-project-tbody .partition-row');
        barRows.forEach(function (tr) {
            var color = tr.dataset.barC || 'transparent';
            tr.style.background = 'linear-gradient(90deg, ' + color + ' 0%, transparent 0%)';
        });
        var island = document.getElementById('harbor-project-tbody').closest('.island');
        function runBarAnimation() {
            barRows.forEach(function (tr, idx) {
                var targetW = parseFloat(tr.dataset.barW) || 0;
                var color = tr.dataset.barC || 'transparent';
                setTimeout(function () {
                    var startTime = null;
                    function step(ts) {
                        if (!startTime) startTime = ts;
                        var progress = Math.min((ts - startTime) / 1200, 1);
                        var eased = 1 - Math.pow(1 - progress, 3);
                        var curW = targetW * eased;
                        tr.style.background = 'linear-gradient(90deg, ' + color + ' ' + curW.toFixed(1) + '%, transparent ' + curW.toFixed(1) + '%)';
                        if (progress < 1) requestAnimationFrame(step);
                    }
                    requestAnimationFrame(step);
                }, idx * 80);
            });
        }
        if (island) {
            var visObs = new IntersectionObserver(function (entries) {
                if (entries[0].isIntersecting) {
                    visObs.disconnect();
                    setTimeout(runBarAnimation, 700);
                }
            }, { threshold: 0.15 });
            visObs.observe(island);
        }
    }

    /* ===== Harbor: API request rate chart ===== */
    async function loadHarborApiChart() {
        showChartLoading('chart-hb-api');
        var sel = '{' + HARBOR_JOB + '}';
        var step = TIME_RANGES[state.range].step;
        var end = Math.floor(Date.now() / 1000);
        var start = end - TIME_RANGES[state.range].seconds;
        var q = 'sum by (method) (rate(harbor_core_http_request_total' + sel + '[5m]))';
        try {
            var result = await k8sRange(q, start, end, step);
            if (!result.length) { showChartEmpty('chart-hb-api', '暂无数据'); return; }
            var palette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];
            var series = result.map(function (item, i) {
                var method = item.metric.method || 'unknown';
                return {
                    name: method,
                    type: 'line',
                    showSymbol: false,
                    smooth: true,
                    lineStyle: { width: 2 },
                    itemStyle: { color: palette[i % palette.length] },
                    data: item.values.map(function (v) { return [v[0] * 1000, parseFloat(v[1])]; })
                };
            });
            renderChart('chart-hb-api', {
                backgroundColor: 'transparent',
                tooltip: Object.assign(baseTooltip(), { valueFormatter: function (v) { return v.toFixed(2) + ' req/s'; } }),
                legend: { top: 0, textStyle: { color: themeColors().text } },
                grid: { left: 60, right: 20, top: 36, bottom: 30 },
                xAxis: timeXAxis(),
                yAxis: baseAxis({ type: 'value', axisLabel: { color: themeColors().text, formatter: '{value}' } }),
                series: series
            });
        } catch (e) { showChartEmpty('chart-hb-api', '加载失败'); }
    }

    /* ===== Harbor: Inflight requests chart ===== */
    async function loadHarborInflightChart() {
        showChartLoading('chart-hb-inflight');
        var sel = '{' + HARBOR_JOB + '}';
        var step = TIME_RANGES[state.range].step;
        var end = Math.floor(Date.now() / 1000);
        var start = end - TIME_RANGES[state.range].seconds;
        var q = 'harbor_core_http_inflight_requests' + sel;
        try {
            var result = await k8sRange(q, start, end, step);
            if (!result.length) { showChartEmpty('chart-hb-inflight', '暂无数据'); return; }
            var series = result.map(function (item) {
                return {
                    name: item.metric.instance || 'harbor',
                    type: 'line',
                    showSymbol: false,
                    smooth: true,
                    lineStyle: { width: 2 },
                    itemStyle: { color: '#3b82f6' },
                    areaStyle: { color: hexToRgba('#3b82f6', 0.15) },
                    data: item.values.map(function (v) { return [v[0] * 1000, parseFloat(v[1])]; })
                };
            });
            renderChart('chart-hb-inflight', {
                backgroundColor: 'transparent',
                tooltip: baseTooltip(),
                legend: { top: 0, textStyle: { color: themeColors().text } },
                grid: { left: 50, right: 20, top: 36, bottom: 30 },
                xAxis: timeXAxis(),
                yAxis: baseAxis({ type: 'value', axisLabel: { color: themeColors().text } }),
                series: series
            });
        } catch (e) { showChartEmpty('chart-hb-inflight', '加载失败'); }
    }

    /* ===== Harbor: Task queue size chart ===== */
    async function loadHarborQueueChart() {
        showChartLoading('chart-hb-queue');
        var sel = '{' + HARBOR_JOB + '}';
        var step = TIME_RANGES[state.range].step;
        var end = Math.floor(Date.now() / 1000);
        var start = end - TIME_RANGES[state.range].seconds;
        var q = 'sum by (type) (harbor_task_queue_size' + sel + ')';
        try {
            var result = await k8sRange(q, start, end, step);
            if (!result.length) { showChartEmpty('chart-hb-queue', '暂无数据'); return; }
            var palette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6'];
            var series = result.map(function (item, i) {
                var qtype = item.metric.type || 'unknown';
                return {
                    name: qtype,
                    type: 'line',
                    showSymbol: false,
                    smooth: true,
                    stack: 'total',
                    lineStyle: { width: 1.5 },
                    itemStyle: { color: palette[i % palette.length] },
                    areaStyle: { opacity: 0.3 },
                    data: item.values.map(function (v) { return [v[0] * 1000, parseFloat(v[1])]; })
                };
            });
            renderChart('chart-hb-queue', {
                backgroundColor: 'transparent',
                tooltip: baseTooltip(),
                legend: { top: 0, textStyle: { color: themeColors().text }, type: 'scroll' },
                grid: { left: 50, right: 20, top: 36, bottom: 30 },
                xAxis: timeXAxis(),
                yAxis: baseAxis({ type: 'value', axisLabel: { color: themeColors().text } }),
                series: series
            });
        } catch (e) { showChartEmpty('chart-hb-queue', '加载失败'); }
    }

    /* ===== Harbor: Task queue latency chart ===== */
    async function loadHarborLatencyChart() {
        showChartLoading('chart-hb-latency');
        var sel = '{' + HARBOR_JOB + '}';
        var step = TIME_RANGES[state.range].step;
        var end = Math.floor(Date.now() / 1000);
        var start = end - TIME_RANGES[state.range].seconds;
        var q = 'harbor_task_queue_latency' + sel;
        try {
            var result = await k8sRange(q, start, end, step);
            if (!result.length) { showChartEmpty('chart-hb-latency', '暂无数据'); return; }
            var palette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6'];
            var series = result.map(function (item, i) {
                var qtype = item.metric.type || 'unknown';
                return {
                    name: qtype,
                    type: 'line',
                    showSymbol: false,
                    smooth: true,
                    lineStyle: { width: 2 },
                    itemStyle: { color: palette[i % palette.length] },
                    data: item.values.map(function (v) { return [v[0] * 1000, parseFloat(v[1])]; })
                };
            });
            renderChart('chart-hb-latency', {
                backgroundColor: 'transparent',
                tooltip: Object.assign(baseTooltip(), { valueFormatter: function (v) { return v.toFixed(2) + ' s'; } }),
                legend: { top: 0, textStyle: { color: themeColors().text }, type: 'scroll' },
                grid: { left: 60, right: 20, top: 36, bottom: 30 },
                xAxis: timeXAxis(),
                yAxis: baseAxis({ type: 'value', axisLabel: { color: themeColors().text, formatter: '{value}s' } }),
                series: series
            });
        } catch (e) { showChartEmpty('chart-hb-latency', '加载失败'); }
    }

    /* ===== Harbor: Refresh orchestration ===== */
    async function refreshHarbor() {
        var banner = document.getElementById('error-banner');
        try {
            await loadHarborOverview();
            banner.hidden = true;
        } catch (e) {
            banner.hidden = false;
            return;
        }
        await Promise.all([
            loadHarborProjectTable().catch(function () {}),
            loadHarborApiChart().catch(function () {}),
            loadHarborInflightChart().catch(function () {}),
            loadHarborQueueChart().catch(function () {}),
            loadHarborLatencyChart().catch(function () {})
        ]);
        var now = new Date();
        document.getElementById('last-refresh').textContent = '上次刷新: ' +
            String(now.getHours()).padStart(2, '0') + ':' +
            String(now.getMinutes()).padStart(2, '0') + ':' +
            String(now.getSeconds()).padStart(2, '0');
        countdown = REFRESH_INTERVAL;
    }

    /* ===== Theme re-apply for all charts ===== */
    function rethemeCharts() {
        Object.keys(chartOpts).forEach(function (id) {
            const c = charts[id];
            if (!c) return;
            // Re-set option with refreshed theme colors by re-running the option builder is complex;
            // simplest: re-apply axis/tooltip/legend colors via merge.
            const tc = themeColors();
            const opt = chartOpts[id];
            if (opt.tooltip) {
                opt.tooltip.backgroundColor = tc.surface;
                opt.tooltip.borderColor = tc.border;
                opt.tooltip.textStyle = { color: tc.textStrong };
            }
            if (opt.legend && opt.legend.textStyle) opt.legend.textStyle.color = tc.text;
            function fixAxis(ax) {
                if (!ax) return;
                const arr = Array.isArray(ax) ? ax : [ax];
                arr.forEach(function (a) {
                    if (a.axisLabel) a.axisLabel.color = tc.text;
                    if (a.axisLine && a.axisLine.lineStyle) a.axisLine.lineStyle.color = tc.border;
                    if (a.splitLine && a.splitLine.lineStyle) a.splitLine.lineStyle.color = tc.border;
                    if (a.nameTextStyle) a.nameTextStyle.color = tc.text;
                });
            }
            fixAxis(opt.xAxis);
            fixAxis(opt.yAxis);
            c.setOption(opt, false);
        });
    }

    /* ===== Refresh orchestration ===== */
    let refreshTimer = null;
    let countdown = REFRESH_INTERVAL;

    async function refreshAll() {
        const banner = document.getElementById('error-banner');
        try {
            await loadOverview();
            state.promOK = true;
            banner.hidden = true;
        } catch (e) {
            state.promOK = false;
            banner.hidden = false;
            return;
        }
        // Parallel load of all selector-dependent panels
        await Promise.all([
            loadOverviewSparks().catch(function () {}),
            loadResourceTable().catch(function () {}),
            loadP99Table().catch(function () {}),
            loadPartitionTable().catch(function () {}),
            loadCpuChart().catch(function () {}),
            loadMemChart().catch(function () {}),
            loadDiskChart().catch(function () {}),
            loadLoadChart().catch(function () {}),
            loadNetChart().catch(function () {}),
            loadBargauge().catch(function () {}),
            loadAggLoad().catch(function () {}),
            loadAggMem().catch(function () {}),
            loadAggDisk().catch(function () {})
        ]);
        const now = new Date();
        document.getElementById('last-refresh').textContent = '上次刷新: ' +
            String(now.getHours()).padStart(2, '0') + ':' +
            String(now.getMinutes()).padStart(2, '0') + ':' +
            String(now.getSeconds()).padStart(2, '0');
        countdown = REFRESH_INTERVAL;
    }

    function startRefreshTimer() {
        if (refreshTimer) clearInterval(refreshTimer);
        countdown = REFRESH_INTERVAL;
        refreshTimer = setInterval(function () {
            countdown--;
            document.getElementById('next-refresh').textContent = '下次刷新: ' + countdown + 's';
            if (countdown <= 0) {
                if (state.activeTab === 'harbor') { refreshHarbor(); }
                else { refreshAll(); }
            }
        }, 1000);
    }

    /* ===== Selector handlers ===== */
    function bindControls() {
        document.getElementById('time-selector').addEventListener('click', function (e) {
            const btn = e.target.closest('.time-btn');
            if (!btn) return;
            document.querySelectorAll('.time-btn').forEach(function (b) { b.classList.remove('active'); });
            btn.classList.add('active');
            state.range = btn.dataset.range;
            if (state.activeTab === 'harbor') {
                refreshHarbor();
            } else {
                refreshAll();
            }
        });
        document.getElementById('site-selector').addEventListener('change', function (e) {
            state.site = e.target.value;
            Promise.all([
                loadResourceTable().catch(function () {}),
                loadP99Table().catch(function () {}),
                loadPartitionTable().catch(function () {}),
                loadCpuChart().catch(function () {}),
                loadMemChart().catch(function () {}),
                loadDiskChart().catch(function () {}),
                loadLoadChart().catch(function () {}),
                loadNetChart().catch(function () {}),
                loadBargauge().catch(function () {}),
                loadAggLoad().catch(function () {}),
                loadAggMem().catch(function () {}),
                loadAggDisk().catch(function () {})
            ]);
        });
    }

    /* ===== Tab routing ===== */
    function switchTab(tab) {
        if (tab !== 'mirrors' && tab !== 'harbor') tab = 'mirrors';
        state.activeTab = tab;
        document.querySelectorAll('.tab-link').forEach(function (link) {
            link.classList.toggle('active', link.dataset.tab === tab);
        });
        var panelMirrors = document.getElementById('panel-mirrors');
        var panelHarbor = document.getElementById('panel-harbor');
        var siteSel = document.getElementById('site-selector');
        if (tab === 'harbor') {
            panelMirrors.hidden = true;
            panelHarbor.hidden = false;
            siteSel.style.display = 'none';
        } else {
            panelMirrors.hidden = false;
            panelHarbor.hidden = true;
            siteSel.style.display = '';
        }
        if (refreshTimer) clearInterval(refreshTimer);
        document.getElementById('next-refresh').textContent = '下次刷新: ' + REFRESH_INTERVAL + 's';
        var panel = tab === 'harbor' ? panelHarbor : panelMirrors;
        var panelCharts = panel.querySelectorAll('.chart');
        setTimeout(function () {
            panelCharts.forEach(function (el) {
                var inst = echarts.getInstanceByDom(el);
                if (inst) inst.resize();
            });
        }, 50);
        if (tab === 'harbor') {
            refreshHarbor();
        } else {
            refreshAll();
        }
        startRefreshTimer();
    }

    /* ===== Resize handling ===== */
    let resizeTO = null;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTO);
        resizeTO = setTimeout(function () {
            Object.keys(charts).forEach(function (id) { if (charts[id]) charts[id].resize(); });
        }, 200);
    });

    /* ===== Theme observer ===== */
    const themeObs = new MutationObserver(function (mutations) {
        mutations.forEach(function (m) {
            if (m.attributeName === 'class') { rethemeCharts(); }
        });
    });
    themeObs.observe(document.body, { attributes: true, attributeFilter: ['class'] });

    /* ===== Init ===== */
    function init() {
        document.getElementById('copyright-year').textContent = new Date().getFullYear();
        var chartIds = ['chart-cpu','chart-mem','chart-disk','chart-load','chart-net','chart-bargauge','chart-agg-load','chart-agg-mem','chart-agg-disk',
                        'chart-hb-api','chart-hb-inflight','chart-hb-queue','chart-hb-latency'];
        chartIds.forEach(function (id) { chartFirstLoad.add(id); });
        bindControls();
        window.addEventListener('hashchange', function () {
            var hash = (window.location.hash || '#mirrors').slice(1);
            switchTab(hash);
        });
        var initialTab = (window.location.hash || '#mirrors').slice(1);
        if (initialTab === 'harbor') {
            switchTab('harbor');
        } else {
            if (window.location.hash && initialTab !== 'mirrors') {
                window.location.hash = '#mirrors';
            }
            refreshAll();
            startRefreshTimer();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
