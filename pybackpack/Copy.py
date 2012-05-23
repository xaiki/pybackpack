import gtk
import os
import stat
from shutil import copy2

def RecursiveCount(path):
	count = 1
	if os.path.isdir(path):
		for e in os.listdir(path):
			count += RecursiveCount(os.path.join(path, e))
	return count

def RecursiveSize(path):
	size = 0
	for e in os.listdir(path):
		size += os.path.getsize(os.path.join(path, e))
		if not os.path.isdir(os.path.join(path, e)):
			pass
		else:
			size += RecursiveSize(os.path.join(path, e))
	return size

def RecursiveCopy(path, dest, callback=None):
	for e in os.listdir(path):
		if callback is not None:
			callback(os.path.join(path, e))
		if not os.path.isdir(os.path.join(path, e)):
			copy2(os.path.join(path, e), os.path.join(dest, e))
			os.chmod(os.path.join(dest, e), os.stat(os.path.join(path, e)).st_mode|stat.S_IWUSR)
		else:
			os.makedirs(os.path.join(dest, e))
			RecursiveCopy(os.path.join(path, e), os.path.join(dest, e), callback)
