#!/usr/bin/python3

# Copyright 2018 Peter Green
# Released under the MIT/Expat license, see doc/COPYING

import os
import sys
import hashlib
import gzip
import urllib.request
import stat
#from sortedcontainers import SortedDict
#from sortedcontainers import SortedList
from collections import deque
from collections import OrderedDict
from datetime import datetime
from email.utils import parsedate_to_datetime
import argparse
import re
from heapq import heappush, heappop
import fcntl

parser = argparse.ArgumentParser(description="mirror raspbian repo.")
parser.add_argument("baseurl", help="base url for source repo (e.g. https://archive.raspbian.org/ )",nargs='?')
parser.add_argument("mdurl", help="base url for mirrordirector or local source mirror (e.g. https://mirrordirector.raspbian.org/ )",nargs='?')
parser.add_argument("hpurl", help="base url for last result hash pool (e.g. http://snapshot.raspbian.org/hashpool )",nargs='?')

parser.add_argument("--internal", help=argparse.SUPPRESS) #base URL for private repo (internal use only)
parser.add_argument("--sourcepool", help="specify a source pool to look for packages in before downloading them (useful if maintaining multiple mirrors)",action='append')
parser.add_argument("--tmpdir", help="specify a temporary directory to avoid storing temporary files in the output tree, must be on the same filesystem as the output tree")

#debug option to set the index file used for the "downloadnew" phase but not the "finalize" phase, used to test error recovery.
parser.add_argument("--debugfif", help=argparse.SUPPRESS)
#debug option to set the source url used to download "dists" files during the "downloadnew" phase, used to test error recovery.
parser.add_argument("--debugfdistsurl", help=argparse.SUPPRESS)

parser.add_argument("--tlwhitelist", help="specify comma-seperated whitelist of top-level directories")

parser.add_argument("--cleanup",help="scan for and remove files not managed by raspbmirror from mirror tree", action="store_true")

parser.add_argument("--debugskippool",help="skip downloading pool data, only download metadata (for debugging)",action="store_true")

parser.add_argument("--distswhitelist", help="specify comman seperated list of distributions")

args = parser.parse_args()

lockfd = os.open('.',os.O_RDONLY)
fcntl.flock(lockfd,fcntl.LOCK_EX | fcntl.LOCK_NB)

def addfilefromdebarchive(filestoverify,filequeue,filename,sha256,size):
	size = int(size)
	sha256andsize = [sha256,size,'M']
	if filename in filestoverify:
		if (sha256andsize[0:2] != filestoverify[filename][0:2]):
			if stage == 'scanexisting':
				print('warning: same file with different hash/size during scanexisting phase old:'+repr(filestoverify[filename])+' new:'+repr(sha256andsize))
				#find existing sha1/size of file on disk if it exists
				if os.path.isfile(filename):
					f = open(filename,'rb')
					data = f.read()
					f.close()
					sha256hash = hashlib.sha256(data)
					sha256hashed = sha256hash.hexdigest().encode('ascii')
					size = len(data)
				else:
					#otherwise we have no idea
					sha256 = None
					size = None
				filestoverify[filename] = [sha256,size,'M']
			else:
				print('error: same file with different hash/size during downloadnew phase old:'+repr(filestoverify[filename])+' new:'+repr(sha256andsize))
				sys.exit(1)
	else:
		filestoverify[filename] = sha256andsize
		addtofilequeue(filequeue,filename)

def addtofilequeue(filequeue,filename):
	filenamesplit = filename.split(b'/')
	if b'dists' in filenamesplit:
		if filename.endswith(b'.gz'):
			# process gz files with high priority so they can be used as substitutes for their uncompressed counterparts
			heappush(filequeue,(10,filename))
		else:
			heappush(filequeue,(20,filename))
	heappush(filequeue,(30,filename))


#regex used for filename sanity checks
pfnallowed = re.compile(b'[a-z0-9A-Z\-_:\+~\.]+',re.ASCII)
shaallowed = re.compile(b'[a-z0-9]+',re.ASCII)

def ensuresafepath(path):
	pathsplit = path.split(b'/')
	if path[0] == '/':
		print("path must be relative")
		sys.exit(1)
	for component in pathsplit:
		if not pfnallowed.fullmatch(component):
			print("file name contains unexpected characters")
			sys.exit(1)
		elif component[0] == '.':
			print("filenames starting with a dot are not allowed")
			sys.exit(1)
	
def geturl(fileurl):
	with urllib.request.urlopen(fileurl.decode('ascii')) as response:
		data = response.read()
		ts = getts(fileurl, response)
	return (data,ts)


def getts(fileurl, response):
	if fileurl[:7] == b'file://':
		ts = os.path.getmtime(fileurl[7:])
	else:
		dt = parsedate_to_datetime(response.getheader('Last-Modified'))
		if dt.tzinfo is None:
			dt = dt.replace(tzinfo=timezone.utc)
		ts = dt.timestamp()
	return ts


def makenewpath(path):
	if args.tmpdir is None:
		return path+b'.new'
	else:
		return os.path.join(args.tmpdir.encode('ascii'),(path+b'.new').replace(b'/',b'~'))

def getfile(path,sha256,size):
	ensuresafepath(path)
	if not shaallowed.fullmatch(sha256):
		print('invalid character in sha256 hash')
		sys.exit(1)
	#hashfn = b'../hashpool/' + sha256[:2] +b'/'+ sha256[:4] +b'/'+ sha256
	#if os.path.isfile(hashfn):
	#	if os.path.getsize(hashfn) != size:
	#		print('size mismatch on existing file in hash pool')
	#		sys.exit(1)
	#else:
	#	secondhashfn = None
	#	if args.secondpool is not None:
	#		secondhashfn = os.path.join(args.secondpool.encode('ascii'),sha256[:2] +b'/'+ sha256[:4] +b'/'+ sha256)
	#		#print(secondhashfn)
	#		if not os.path.isfile(secondhashfn):
	#			secondhashfn = None
	#	if secondhashfn is None:
	#	else:
	#		print('copying '+path.decode('ascii')+' with hash '+sha256.decode('ascii')+' from secondary pool')
	#		f = open(secondhashfn,'rb')
	#		data = f.read()
	#		f.close()
	#		ts = os.path.getmtime(secondhashfn)
	#	sha256hash = hashlib.sha256(data)
	#	sha256hashed = sha256hash.hexdigest().encode('ascii')
	#	if (sha256 != sha256hashed):
	#		#print(repr(filesize))
	#		#print(repr(sha256))
	#		#print(repr(sha256hashed))
	#		print('hash mismatch while downloading file '+path.decode('ascii')+' '+sha256.decode('ascii')+' '+sha256hashed.decode('ascii'));
	#		sys.exit(1)
	#	if len(data) != size:
	#		print('size mismatch while downloading file')
	#		sys.exit(1)
	#	hashdir = os.path.dirname(hashfn)
	#	os.makedirs(hashdir,exist_ok=True)
	#	f = open(hashfn,'wb')
	#	f.write(data)
	#	f.close()
	#	            
	#	os.utime(hashfn,(ts,ts))
	if len(os.path.dirname(path)) > 0:
		os.makedirs(os.path.dirname(path),exist_ok=True)
	if os.path.isfile(makenewpath(path)): # "new" file already exists, lets check the hash
		fn = makenewpath(path)
		sha256hashed, tl = getfilesha256andsize(fn)
		if (sha256 == sha256hashed) and (size == tl):
			print('existing file '+path.decode('ascii')+' matched by hash and size')
			fileupdates.add(path)
			return # no download needed but rename is
	elif path in oldknownfiles: 
		#shortcut exit if file is unchanged, we skip this if a "new" file was detected because
		#that means some sort of update was going on to the file and may need to be finished/cleaned up.
		oldsha256,oldsize,oldstatus = oldknownfiles[path]
		if (oldsha256 == sha256) and (oldsize == size) and (oldstatus != 'F'):
			return # no update needed
	if os.path.isfile(path): # file already exists
		if (size == os.path.getsize(path)): #no point reading the data and calculating a hash if the size does not match
			sha256hashed, tl = getfilesha256andsize(path)
			if (sha256 == sha256hashed) and (size == tl):
				print('existing file '+path.decode('ascii')+' matched by hash and size')
				if os.path.isfile(makenewpath(path)):
					#if file is up to date but a "new" file exists and is bad
					#(we wouldn't have got this far if it was good)
					#schedule the "new" file for removal by adding it to "basefiles"
					basefiles.add(makenewpath(path))
				return  # no update needed
	if os.path.isfile(path): # file already exists
		fileupdates.add(path)
		if os.path.isfile(makenewpath(path)):
			os.remove(makenewpath(path))
		outputpath = makenewpath(path)
	else:
		outputpath = path
	pathsplit = path.split(b'/')
	if (pathsplit[1:2] == [b'pool']) and (args.debugskippool):
		print('skipping download of '+path.decode('ascii')+' because --debugskippool was specified')
		return
	if (args.internal is not None) and (pathsplit[0] == b'raspbian'):
		fileurl = args.internal.encode('ascii') +b'/private/' + b'/'.join(pathsplit[1:])
	else:
		fileurl = baseurl + b'/' + path
	data = None
	if args.sourcepool is not None:
		for sourcepool in args.sourcepool:
			#print(repr(args.sourcepool))
			#print(repr(sourcepool))
			sourcepool = sourcepool.encode('ascii')
			if pathsplit[1] == b'pool':
				spp = os.path.join(sourcepool,b'/'.join(pathsplit[2:]))
				if os.path.isfile(spp)  and (size == os.path.getsize(spp)):
					print('trying file from sourcepool '+spp.decode('ascii'))
					ts = os.path.getmtime(spp)
					f = open(spp,'rb')
					data = f.read()
					f.close()
					sha256hash = hashlib.sha256(data)
					sha256hashed = sha256hash.hexdigest().encode('ascii')
					if (sha256 != sha256hashed):
						#print(repr(filesize))
						#print(repr(sha256))
						#print(repr(sha256hashed))
						print('hash mismatch while trying file from sourcepool, ignoring file');
						data = None
						continue
					try:
						os.link(spp,outputpath)
						print('successfully hardlinked file to source pool')
					
					except:
						print('file in souce pool was good but hard linking failed, copying file instead')
					fdownloads.write(outputpath+b'\n')
					fdownloads.flush()
					return
	if data is None:
		if path+b'.gz' in knownfiles:
			if path+b'.gz' in fileupdates:
				gzfile = makenewpath(path+b'.gz')
			else:
				gzfile = path+b'.gz'
			print('uncompressing '+gzfile.decode('ascii')+' with hash '+sha256.decode('ascii')+' to '+outputpath.decode('ascii'))
			f = gzip.open(gzfile)
			data = f.read()
			f.close()
			ts = os.path.getmtime(gzfile)
			if not checkdatahash(data, sha256, 'hash mismatch while uncompressing file ', path, ''):
				sys.exit(1)
			if len(data) != size:
				print('size mismatch while uncompressing file')
				sys.exit(1)

	#use slicing so we don't error if pathsplit only has one item
	if (data is None) and (mdurl is not None) and (pathsplit[1:2] == [b'pool']):

		fileurl = mdurl + b'/' + path
		#fileurl = mdurl + b'/' + b'/'.join(pathsplit[1:])
		data, ts = getandcheckfile(fileurl, sha256, size, path, outputpath, ' from mirrordirector',' trying main server instead')
	if data is None:

		if (args.internal is not None) and (pathsplit[0] == b'raspbian'):
			fileurl = args.internal.encode('ascii') +b'/private/' + b'/'.join(pathsplit[1:])
		elif (args.debugfdistsurl is not None) and (stage == 'downloadnew') and (b'dists' in pathsplit):
			fileurl = args.debugfdistsurl.encode('ascii') + b'/' + path
		else:
			fileurl = baseurl + b'/' + path
		data, ts = getandcheckfile(fileurl, sha256, size, path, outputpath, '','')
	if data is None:
		if (stage == 'downloadnew') and (b'dists' not in pathsplit):
			print('continuing dispite download failure of '+path.decode('ascii')+', may revisit later')
			global dlerrorcount
			dlerrorcount += 1
			knownfiles[path][2] = 'F'
			return
	if (data is None) and (hpurl is not None):
		print('failed to get '+path.decode('ascii')+' from normal sources, trying hash pool')
		ensuresafepath(sha256)
		fileurl = hpurl + b'/' + sha256[0:2] + b'/' + sha256[0:4] + b'/' + sha256
		data, ts = getandcheckfile(fileurl, sha256, size, path, outputpath, '', '')
	if data is None:
		print('failed to get '+path.decode('ascii')+' aborting')
		sys.exit(1)
	if data is not ...: #... is used to indicate that the file has been downloaded directly to disk and we don't
		                # need to write it out here.
		f = open(outputpath,'wb')
		f.write(data)
		f.close()
	os.utime(outputpath,(ts,ts))
	fdownloads.write(outputpath+b'\n')
	fdownloads.flush()


def getfilesha256andsize(fn):
	sha256hash = hashlib.sha256()
	f = open(fn, 'rb')
	l = bs
	tl = 0
	while l == bs:
		data = f.read(bs)
		l = len(data)
		tl += l
		sha256hash.update(data)
	f.close()
	sha256hashed = sha256hash.hexdigest().encode('ascii')
	return sha256hashed, tl


bs = 16 * 1024 * 1024

def getandcheckfile(fileurl, sha256, size, path, outputpath, errorfromstr, errorsuffix):
	f = None
	try:

		sha256hash = hashlib.sha256()
		if path == outputpath:
			writepath = makenewpath(path)
			viamsg = ' via '+writepath.decode('ascii')
		else:
			writepath = outputpath
			viamsg = ''
		print(
			'downloading ' + fileurl.decode('ascii') + ' with hash ' + sha256.decode(
				'ascii') + ' to ' + outputpath.decode(
				'ascii') + viamsg)
		f = open(writepath, 'wb')
		with urllib.request.urlopen(fileurl.decode('ascii')) as response:
			l = bs
			tl = 0
			while l == bs:
				data = response.read(bs)
				f.write(data)
				l = len(data)
				tl += l
				sha256hash.update(data)
			ts = getts(fileurl, response)

			data = ... #used as a flag to indicate that the data is written to disk rather than stored in memory
		f.close()
		if not testandreporthash(sha256hash, sha256, 'hash mismatch while downloading file' + errorfromstr + ' ', path,
							 errorsuffix):
			data = None
		elif tl != size:
			print('size mismatch while downloading file' + errorfromstr + '.' + errorsuffix)
			data = None
	except Exception as e:
		print('exception ' + str(e) + ' while downloading file' + errorfromstr + '.' + errorsuffix)
		if f is not None:
			f.close()
		data = None
		ts = None
	if data is not None:
		#success
		if writepath != outputpath:
			os.rename(writepath, outputpath)
	else:
		#failure, cleanup writepath if nessacery
		if os.path.exists(writepath):
			os.remove(writepath)

	return data, ts


def checkdatahash(data, sha256, errorprefix, path, errorsuffix):
	sha256hash = hashlib.sha256(data)
	return testandreporthash(sha256hash, sha256, errorprefix, path, errorsuffix)


def testandreporthash(sha256hash, sha256, errorprefix, path, errorsuffix):
	sha256hashed = sha256hash.hexdigest().encode('ascii')
	if (sha256 != sha256hashed):
		# print(repr(filesize))
		# print(repr(sha256))
		# print(repr(sha256hashed))
		print(errorprefix + path.decode('ascii') + ' ' + sha256.decode('ascii') + ' ' + sha256hashed.decode(
			'ascii') + errorsuffix);
		return False
	return True


if (args.mdurl is None) or (args.mdurl.upper() == 'NONE'):
	mdurl = None
else:
	mdurl = args.mdurl.encode('ascii')

if (args.hpurl is None) or (args.hpurl.upper() == 'NONE'):
	hpurl = None
else:
	hpurl = args.hpurl.encode('ascii')

if args.baseurl is None:
	baseurl = b'https://archive.raspbian.org'
	mdurl = b'http://mirrordirector.raspbian.org'
	hpurl = b'http://snapshot.raspbian.org/hashpool'
else:
	baseurl = args.baseurl.encode('ascii')




symlinkupdates = list()
fileupdates = set()

def opengu(filepath):
	#print('in opengu')
	#print('filepath = '+repr(filepath))
	#print('fileupdates = '+repr(fileupdates))
	f = None
	if (filepath in fileupdates):
		print((b'opening '+makenewpath(filepath)+b' for '+filepath).decode('ascii'))
		f = open(makenewpath(filepath),'rb')
	elif (filepath+b'.gz' in fileupdates):
		print((b'opening '+makenewpath(filepath+b'.gz')+b' for '+filepath).decode('ascii'))
		f = gzip.open(makenewpath(filepath+b'.gz'),'rb')
	elif os.path.exists(filepath):
		print((b'opening '+filepath+b' for '+filepath).decode('ascii'))
		f = open(filepath,'rb')
	elif os.path.exists(filepath+b'.gz'):
		print((b'opening '+filepath+b'.gz for '+filepath).decode('ascii'))
		f = gzip.open(filepath+b'.gz','rb')
	return f

oldsymlinks = set()
newsymlinks = set()

fdownloads = open(makenewpath(b'raspbmirrordownloads.txt'),"ab")

dlerrorcount = 0;

for stage in ("scanexisting","downloadnew","finalize"):
	if stage == "finalize":
		if dlerrorcount == 0:
			print('skipping stage 3 as there were no download failures in stage 2')
			#we can finish now.
			break
		print('stage 3, download final updates')
		
		oldknownfiles = knownfiles
		oldsymlinks |= newsymlinks
		newsymlinks = set()

	if stage == "downloadnew":
		print('stage 2, main download')
		oldknownfiles = knownfiles
		basefiles = set(oldknownfiles.keys())

	if stage == "scanexisting":
		print('stage 1, scan existing')
	else:
		if args.internal is not None:
			fileurl = args.internal.encode('ascii') + b'/snapshotindex.txt'
		else:
			fileurl = baseurl +b'/snapshotindex.txt'

		if (stage == "downloadnew") and (args.debugfif is not None):
			fileurl = args.debugfif.encode('ascii')
		(filedata,ts) = geturl(fileurl) 

		f = open(makenewpath(b'snapshotindex.txt'),'wb')
		if (args.tlwhitelist is None) and (args.distswhitelist is None):
			f.write(filedata)
		else:
			lines = filedata.split(b'\n')
			if lines[-1] == b'':
				del(lines[-1])
			if args.tlwhitelist is not None:
				tlwhitelist = set(args.tlwhitelist.encode('ascii').split(b','))
				linesnew = []
				for line in lines:
					linesplit = line.split(b'/')
					if linesplit[0] in tlwhitelist:
						linesnew.append(line)
				lines = linesnew
			if args.distswhitelist is not None:
				distswhitelist = set(args.distswhitelist.encode('ascii').split(b','))
				founddists = set()
				foundesdists = set()
				linesnew = []
				for line in lines:
					path, sizeandsha = line.split(b' ')
					pathsplit = path.split(b'/')
					#print(pathsplit)
					#print(len(pathsplit))
					if (len(pathsplit) > 2) and (pathsplit[1] == b'dists'):
						if sizeandsha[0:2] == b'->': #symlink
							target = sizeandsha[2:]
							if target in distswhitelist:
								linesnew.append(line)
						elif pathsplit[2] in distswhitelist:
							linesnew.append(line)
							founddists.add((pathsplit[0],pathsplit[2]))
							if (len(pathsplit) > 3) and (pathsplit[3] == b'extrasources'):
								foundesdists.add((pathsplit[0],pathsplit[2]))
					elif (len(pathsplit) > 1) and pathsplit[1] == b'pool':
						pass
					else:
						linesnew.append(line)
					
				lines = linesnew
				if founddists == set():
					print('none of the whitelisted distributions were found in the index file')
					sys.exit(1)
				missingesdists = founddists - foundesdists
				if missingesdists != set():
					for toplevel,distribution in missingesdists:
						print((b'missing extra sources file for '+toplevel+b'/dists/'+distribution).decode('ascii'))
					sys.exit(1)
			for line in lines:
				f.write(line+b'\n')
		f.close()
		os.utime(makenewpath(b'snapshotindex.txt'),(ts,ts))

	knownfiles = OrderedDict()
	filequeue = []

	if stage == "scanexisting":
		if os.path.isfile(b'snapshotindex.txt'):
			f = open(b'snapshotindex.txt','rb')
		else:
			continue
	else:
		f = open(makenewpath(b'snapshotindex.txt'),'rb')
	for line in f:
		line = line.strip()
		filepath, sizeandsha = line.split(b' ')
		if sizeandsha[:2] == b'->':
			symlinktarget = sizeandsha[2:]
			ensuresafepath(filepath)
			ensuresafepath(symlinktarget)
			if len(os.path.dirname(filepath)) > 0:
				os.makedirs(os.path.dirname(filepath),exist_ok=True)
			if stage == "scanexisting":
				oldsymlinks.add(filepath)
			else:
				if os.path.islink(filepath):
					if os.readlink(filepath) != symlinktarget:
						symlinkupdates.append((filepath,symlinktarget))
				else:
					print('creating symlink '+filepath.decode('ascii')+' -> '+symlinktarget.decode('ascii'))
					os.symlink(symlinktarget,filepath)
				newsymlinks.add(filepath)
		else:
			size,sha256 = sizeandsha.split(b':')
			size = int(size)
			knownfiles[filepath] = [sha256,size,'R']
			addtofilequeue(filequeue,filepath)

	f.close()

	extrasources = {}
	while filequeue:
		(priority, filepath) = heappop(filequeue)
		#print('processing '+filepath.decode('ascii'))
		sha256,size,status = knownfiles[filepath]
		if (stage != "scanexisting") and ((filepath+b'.gz' not in knownfiles) or (status == 'R') or os.path.exists(filepath)):
			getfile(filepath,sha256,size)
		pathsplit = filepath.split(b'/')
		#print(pathsplit[-1])
		#if (pathsplit[-1] == b'Packages'):
		#	print(repr(pathsplit))
		if (pathsplit[-1] == b'Release') and (pathsplit[-3] == b'dists'):
			distdir = b'/'.join(pathsplit[:-1])
			f = opengu(filepath)
			if f is None:
				if stage == 'scanexisting':
					print('warning: cannot find '+filepath.decode('ascii')+' while scanning existing state')
					continue
				else:
					print('error: cannot find '+filepath.decode('ascii')+' or a gzipped substitute, aborting')
					sys.exit(1)
			insha256 = False;
			for line in f:
				#print(repr(line[0]))
				if (line == b'SHA256:\n'):
					insha256 = True
				elif ((line[0] == 32) and insha256):
					linesplit = line.split()
					filename = distdir+b'/'+linesplit[2]
					#if filename in knownfiles:
					#	if files
					#print(filename)
					addfilefromdebarchive(knownfiles,filequeue,filename,linesplit[0],linesplit[1]);
				else:
					insha256 = False
			f.close()
		elif (pathsplit[-1] == b'Packages') and ((pathsplit[-5] == b'dists') or ((pathsplit[-3] == b'debian-installer') and (pathsplit[-6] == b'dists'))):
						if pathsplit[-5] == b'dists':
							toplevel = b'/'.join(pathsplit[:-5])
						else:
							toplevel = b'/'.join(pathsplit[:-6])
						print('found packages file: '+filepath.decode('ascii'))
						pf = opengu(filepath)
						if pf is None:
							if stage == 'scanexisting':
								print('warning: cannot find '+filepath.decode('ascii')+' while scanning existing state')
								continue
							else:
								print('error: cannot find '+filepath.decode('ascii')+' or a gzipped substitute, aborting')
								sys.exit(1)

						filename = None
						size = None
						sha256 = None
							
						for line in pf:
							linesplit = line.split()
							if (len(linesplit) == 0):
								if (filename != None):
									addfilefromdebarchive(knownfiles,filequeue,filename,sha256,size);
								filename = None
								size = None
								sha256 = None
							elif (linesplit[0] == b'Filename:'):
								filename = toplevel+b'/'+linesplit[1]
							elif (linesplit[0] == b'Size:'):
								size = linesplit[1]
							elif (linesplit[0] == b'SHA256:'):
								sha256 = linesplit[1]
						pf.close()
		elif (pathsplit[-1] == b'Sources') and (pathsplit[-5] == b'dists'):
						print('found sources file: '+filepath.decode('ascii'))
						toplevel = b'/'.join(pathsplit[:-5])
						pf = opengu(filepath)
						if pf is None:
							if stage == 'scanexisting':
								print('warning: cannot find '+filepath.decode('ascii')+' while scanning existing state')
								continue
							else:
								print('error: cannot find '+filepath.decode('ascii')+' or a gzipped substitute, aborting')
								sys.exit(1)
						filesfound = [];
						directory = None
						insha256p = False;
						for line in pf:
							linesplit = line.split()
							if (len(linesplit) == 0):
								for ls in filesfound:
									#print(repr(ls))
									addfilefromdebarchive(knownfiles,filequeue,toplevel+b'/'+directory+b'/'+ls[2],ls[0],ls[1]);
								filesfound = [];
								directory = None
								insha256p = False
							elif ((line[0] == 32) and insha256p):
								filesfound.append(linesplit)
							elif (linesplit[0] == b'Directory:'):
								insha256p = False
								directory = linesplit[1]
							elif (linesplit[0] == b'Checksums-Sha256:'):
								insha256p = True
							else:
								insha256p = False
						pf.close()
		elif (args.distswhitelist is not None) and (pathsplit[-1] == b'extrasources') and (pathsplit[-3] == b'dists'):
						print('found extrasources file: '+filepath.decode('ascii'))
						esf = opengu(filepath)
						if esf is None:
							if stage == 'scanexisting':
								print('warning: cannot find '+filepath.decode('ascii')+' while scanning existing state')
								continue
							else:
								print('error: cannot find '+filepath.decode('ascii')+' or a gzipped substitute, aborting')
								sys.exit(1)
						for line in esf:
							line = line.strip()
							filename , shaandsize = line.split(b' ')
							size , sha256 = shaandsize.split(b':')
							addfilefromdebarchive(knownfiles,filequeue,filename,sha256,size)
							extrasources[filename] = shaandsize
							#print(line)

fdownloads.close()
fdownloads = open(makenewpath(b'raspbmirrordownloads.txt'),"rb")
for line in fdownloads:
	basefiles.add(line.strip())
fdownloads.close()

def throwerror(error):
	raise error

if args.cleanup:
	towalk = os.walk('.', True, throwerror, False)
	for (dirpath, dirnames, filenames) in towalk:
		for filename in (filenames + dirnames):  # os.walk seems to regard symlinks to directories as directories.
			filepath = os.path.join(dirpath, filename)[2:].encode('ascii')  # [2:] is to strip the ./ prefix
			# print(filepath)
			if os.path.islink(filepath):
				oldsymlinks.add(filepath)
		for filename in filenames:
			filepath = os.path.join(dirpath, filename)[2:].encode('ascii')  # [2:] is to strip the ./ prefix
			if not os.path.islink(filepath) and not filepath.startswith(b'snapshotindex.txt') and not filepath.startswith(b'raspbmirrordownloads.txt'):
				basefiles.add(filepath)

print('stage 4, moves and deletions')

for filepath in fileupdates:
	print((b'renaming '+makenewpath(filepath)+b' to '+filepath).decode('ascii'))
	os.replace(makenewpath(filepath),filepath)

for (filepath,symlinktarget) in symlinkupdates:
	print('updating symlink '+filepath.decode('ascii')+' -> '+symlinktarget.decode('ascii'))
	os.remove(filepath)
	os.symlink(symlinktarget,filepath)


removedfiles = (basefiles | oldsymlinks) - (set(knownfiles.keys()) | newsymlinks)

def isemptydir(dirpath):
	#scandir would be significantly more efficient, but needs python 3.6 or above
	#which is not reasonable to expect at this time.
	#return os.path.isdir(dirpath) and ((next(os.scandir(dirpath), None)) is None)
	return os.path.isdir(dirpath) and (len(os.listdir(dirpath)) == 0)

for filepath in removedfiles:
	#file may not actually exist, either due to earlier updates gone-wrong
	#or due to the file being a non-realised uncompressed version of
	#a gzipped file.
	if os.path.exists(filepath): 
		ensuresafepath(filepath)
		print('removing '+filepath.decode('ascii'))
		os.remove(filepath)
		#clean up empty directories.
		dirpath = os.path.dirname(filepath)
		while (len(dirpath) != 0) and isemptydir(dirpath):
			print('removing empty dir '+dirpath.decode('ascii'))
			os.rmdir(dirpath)
			dirpath = os.path.dirname(dirpath)

f = open(makenewpath(b'snapshotindex.txt'),'ab')
for filename, shaandsize in extrasources.items():
	f.write(filename+b' '+shaandsize+b'\n')
f.close()

os.rename(makenewpath(b'snapshotindex.txt'),b'snapshotindex.txt')
os.remove(makenewpath(b'raspbmirrordownloads.txt'))

