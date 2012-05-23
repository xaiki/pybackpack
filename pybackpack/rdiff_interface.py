import rdiff_backup.Main
import os
import sys
import shutil
import gtk
import gobject
import time
import subprocess

import version
from LogHandler import LogHandler
from ConfigParser import SafeConfigParser, NoOptionError

base = os.environ['HOME']
setspath = "%s/.%s/sets/" % (base, version.APPPATH)

class RdiffError(Exception):
	"""Called when running rdiff-backup fails."""
	def __init__(self, status):
		self.status = status

	def __str__(self):
		return "rdiff-backup exited with status %d\n" % self.status


def Refresh():
	reload(rdiff_backup.Main)

def CheckDestination(path, ignore_rdiff_data=True):
	"""Checks if the path is writeable, and if it's got something in it"""
	if not os.access(path, os.R_OK|os.W_OK|os.X_OK):
		return (False, 'no_permission')
	if os.path.abspath(path) == os.path.abspath(os.environ['HOME']):
		return (False, 'is_home_dir')
	if len(os.listdir(path)) != 0:
		if os.listdir(path).count('rdiff-backup-data') == 1 and ignore_rdiff_data:
			return (True, '')
		else:
			return (False, 'not_empty')
	# OK to write to this path
	return (True, '')

def ParseRestoreSrc(path):
	if len(path) == 0:
		return None
	try:
		contents = os.listdir(path)
	except OSError:
		return None
	if contents == []:
		return None
	if contents.count('%s.set' % version.APPPATH) == 1:
		cp = SafeConfigParser()
		cp.read(os.path.join(path, '%s.set' % version.APPPATH))
		ret = {}
		for key, val in cp.items('Set'):
			ret[key] = val
		ret['increments'] = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
		log = LogHandler()
		sys.stdout = log
		args = ['--list-increments', '--parsable-output', '--terminal-verbosity', '0', path.replace("rdiff-backup-data", "")]
		Refresh()
		try:
			Run_rdiff(args)
		except OSError:
			"""rdiff-backup <= 1.1.9 has a bug where it can't restore from a read-only 
			   location unless it's run as root. Unfortunately there's not much we can
			   do until 1.2.0(?) becomes mainstream. We deal with that bug here."""
			sys.stdout = sys.__stdout__
			for f in os.listdir(path):
				if f[:15] == "current_mirror." or f[:11] == "increments.":
					rawtime = f.replace("current_mirror.", "").replace("increments.", "").replace(".data", "")
					try:
						ret['increments'].insert_before(ret['increments'][0].iter, (rawtime, rawtime))
					except IndexError:
						ret['increments'].append((rawtime, rawtime))
			ret['readonly'] = True
			return ret
		sys.stdout = sys.__stdout__
		for inc in str(log).splitlines():
			timestamp = inc.split()[0]
			try:
				ret['increments'].insert_before(ret['increments'][0].iter, (time.ctime(float(timestamp)), timestamp))
			except IndexError:
				ret['increments'].append((time.ctime(float(timestamp)), timestamp))
		return ret
	elif contents.count('rdiff-backup-data') == 1:
		return ParseRestoreSrc(os.path.join(path, 'rdiff-backup-data'))
	else:
		return None
	return None

def ParseRestoreSSHSrc(user, host, path):
	path = path.replace("/rdiff-backup-data", "")
	if len(path) == 0:
		return None
	args = ['scp',
		'%s@%s:%s/rdiff-backup-data/%s.set' % (user, host, path, version.APPPATH),
		'/tmp/%s.ssh.set' % version.APPPATH]
	scp = subprocess.Popen(args, shell=False)
	while scp.poll() is None:
		gtk.main_iteration()
	cp = SafeConfigParser()
	if cp.read('/tmp/%s.ssh.set' % version.APPPATH) == []:
		return None
	ret = {}
	for key, val in cp.items('Set'):
		ret[key] = val
	ret['increments'] = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
	log = LogHandler()
	sys.stdout = log
	sshpath = "%s@%s::%s" % (user, host, path)
	args = ['--list-increments', '--parsable-output', '--terminal-verbosity', '0', sshpath]
	Refresh()
	try:
		Run_rdiff(args)
	except OSError:
		return None
	sys.stdout = sys.__stdout__
	for inc in str(log).splitlines():
		timestamp = inc.split()[0]
		try:
			ret['increments'].insert_before(ret['increments'][0].iter, (time.ctime(float(timestamp)), timestamp))
		except IndexError:
			ret['increments'].append((time.ctime(float(timestamp)), timestamp))
	return ret
	
def SysExit(status=0):
	raise RdiffError(status)

def BackupSet(set, dest, output=sys.__stdout__, err_output=sys.__stderr__,\
	copy_set_file=True, is_ssh=False, force=False):
	"""Performs a backup of the specified set to the path dest"""
	exitfunction = sys.exit
	sys.exit = SysExit
	arglist = ['--exclude-sockets', '--exclude-fifos', '--exclude-device-files', '--terminal-verbosity', '5', '--verbosity', '9']
	if force:
		arglist.append('--force')
	if not is_ssh:
		arglist.extend(['--exclude', dest])
	arglist.extend(['--include-globbing-filelist', os.path.join(setspath, set.path, "filelist"), "/", dest])
	sys.stdout = output
	sys.stderr = err_output
	Run_rdiff(arglist)
	if copy_set_file:
		shutil.copyfile(os.path.join(setspath, set.path, "set.ini"), os.path.join(dest, "rdiff-backup-data", "%s.set" % version.APPPATH))
	sys.stderr = sys.__stderr__
	sys.stdout = sys.__stdout__
	sys.exit = exitfunction

def Run_rdiff(arglist):
	print >>sys.__stdout__, arglist
	rdiff_backup.Main.parse_cmdlineoptions(arglist)
	if rdiff_backup.Main.Globals.version > "0.13":
		rdiff_backup.Main.check_action()
	if rdiff_backup.Main.Globals.version < "0.13":
		rdiff_backup.Main.set_action()
	cmdpairs = rdiff_backup.Main.SetConnections.get_cmd_pairs(rdiff_backup.Main.args, rdiff_backup.Main.remote_schema, rdiff_backup.Main.remote_cmd)
	rdiff_backup.Main.Security.initialize(rdiff_backup.Main.action or "mirror", cmdpairs)
	rps = map(rdiff_backup.Main.SetConnections.cmdpair2rp, cmdpairs)
	if rdiff_backup.Main.Globals.version > "0.13":
		rdiff_backup.Main.final_set_action(rps)
	rdiff_backup.Main.misc_setup(rps)
	rdiff_backup.Main.take_action(rps)
	rdiff_backup.Main.cleanup()
	

def RestoreSet(src_path, dst_path, output=sys.__stdout__, err_output=sys.__stderr__, increment="now"):
	"""Restores the rdiff-backup backup from src to dst_path"""
	exitfunction = sys.exit
	sys.exit = SysExit
	arglist = ['--force', '--terminal-verbosity', '5', '--verbosity', '9', '-r', increment, src_path, dst_path]
	sys.stdout = output
	sys.stderr = err_output
	try:
		Run_rdiff(arglist)
	except Exception, e:
		sys.stderr.write(_("Error:") + (" %s\n" % e)
                        + _("rdiff-backup version: ") + "%s\n%s " % (rdiff_backup.Main.Globals.version, version.APPNAME)
                        + _("version:") + " %s\n" % version.VERSION)
		raise AssertionError(e)
	sys.stdout = sys.__stdout__
	sys.stderr = sys.__stderr__
	sys.exit = exitfunction
