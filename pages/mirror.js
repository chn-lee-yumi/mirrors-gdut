// 创建表单与输入框
var form = document.createElement('form');
var input = document.createElement('input');

// 设置输入框属性
input.name = 'filter';
input.id = 'search';
input.placeholder = '输入以搜索...';

// 将输入框插入表单
form.appendChild(input);

// 将表单插入到页面中
document.querySelector('h1').after(form);

// 缓存要筛选的行集合
var listItems = [].slice.call(document.querySelectorAll('#distro-table tbody tr'));

// 监听输入框的键盘输入事件
input.addEventListener('keyup', function () {
    var i,
        e = "^(?=.*\\b" + this.value.trim().split(/\s+/).join("\\b)(?=.*\\b") + ").*$",
        n = RegExp(e, "i");
    listItems.forEach(function(item) {
        item.removeAttribute('hidden');
    });
    listItems.filter(function(item) {
        i = item.querySelector('td').textContent.replace(/\s+/g, " ");
        return !n.test(i);
    }).forEach(function(item) {
            item.hidden = true;
    });
});

// 自动切换深色模式
document.addEventListener("DOMContentLoaded", function() {
    // Check if the user's system has dark mode preference
    const prefersDarkMode = window.matchMedia("(prefers-color-scheme: dark)").matches;

    // Apply dark theme if user's system preference is for dark mode
    if (prefersDarkMode) {
        document.body.classList.add("dark-theme");
    }
});