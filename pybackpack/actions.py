import os
import sys
import gtk
import shutil
import mkisofs
import version
import traceback
import subprocess
import rdiff_interface
import gobject
from LogHandler import LogHandler
try:
	import braseroburn
	braseroburn.start()
except ImportError:
	pass


class DestinationError(Exception):
	FAIL_MISC = 1
	FAIL_RD = 2  # Read perm on destination
	FAIL_WR = 4  # Write perm on destination
	FAIL_EX = 8  # Execute perm on destination
	FAIL_HM = 16 # Destination is homedir
	FAIL_MK = 32 # Could not make destination directory
	WARN_NEMPTY = 64 # Not empty

	msgs = {
		FAIL_MISC: '',
		FAIL_RD: _("No read permission on destination directory"),
		FAIL_WR: _("No write permission on destination directory"),
		FAIL_EX: _("No execute permission on destionation directory"),
		FAIL_HM: _("Destination is home directory. This would remove the files in your home directory. Please choose a different location."),
		FAIL_MK: _("Could not create destination directory"),
		WARN_NEMPTY: _("Destination directory is not empty"),
	}

	"""
	An exception to be raised when the backup destination is unsuitable.
	"""
	def __init__(self, code, path, msg=None):
		Exception.__init__(self)
		if msg is None:
			self.message = "%s: %s" % (self.msgs[code], path)
		else:
			self.message = "%s: %s (%s)" % (self.msgs[code], path, msg)
		self.code = code
	
	def __str__(self):
		return self.message

class BackupError(Exception):
	"""
	An exception to be raised when something goes wrong during a backup.
	"""
	pass

class Backup:
	"""
	The base class which provides local backup functionality.
	"""
	def __init__(self):
		"""
		Initialise a Backup object
		"""
		self.progress = -1
		self.progress_cbs = []
		self.destination = None
		self.filecount = 0
		self.force = False

	def set_destination(self, destination):
		"""
		Set the destination directory for the backup.
		"""
		if os.path.abspath(destination) == os.path.abspath(os.environ['HOME']):
			self.destination = None
			raise DestinationError(DestinationError.FAIL_HM,
					destination)
		self.destination = destination

	def add_progress_cb(self, progress_cb, data=None):
		"""
		Set the signal handler for reporting backup progress.
		If data is provided, it will be passed to the handler.
		"""
		self.progress_cbs.append((progress_cb,data))
	
	def report_progress(self, status):
		"""
		Report progress percentage to the progress callbacks.
		"""
		for cb, data in self.progress_cbs:
			if callable(cb):
				cb(self.progress, status, data)
	
	def check_destination(self):
		"""
		Check the destination directory is OK to back up to.
		"""
		if not os.path.exists(self.destination):
			try:
				self.report_progress(
					_("Creating destination directory"))
				os.makedirs(self.destination)
			except OSError, e:
				raise DestinationError(DestinationError.FAIL_MK,
						self.destination, e.strerror)

		home = os.environ['HOME']
		if os.path.abspath(self.destination) == os.path.abspath(home):
			raise DestinationError(DestinationError.FAIL_HM,
					self.destination)
		if not os.access(self.destination, os.R_OK):
			raise DestinationError(DestinationError.FAIL_RD,
					self.destination)
		if not os.access(self.destination, os.W_OK):
			raise DestinationError(DestinationError.FAIL_WR,
					self.destination)
		if not os.access(self.destination, os.X_OK):
			raise DestinationError(DestinationError.FAIL_EX,
					self.destination)

		ls = os.listdir(self.destination)
		if len(ls) > 0:
			if ls.count('rdiff-backup-data') == 0:
				raise DestinationError(
					DestinationError.WARN_NEMPTY, self.destination)


	def __analyze_source(self, bset, ui):
		"""
		Check files are ok to backup and count them.
		"""
		count = 0
		self.report_progress(_("Analyzing source files"))

		for path in bset.files_include:
			if path == bset.dest:
				ui.statuswin.addmsg(_("Destination directory in backup source. Omitting."))
			elif os.path.isdir(path):
				for dirname, dirs, files in os.walk(path):
					for f in files:
						fullpath = os.path.join(dirname, f)
						if fullpath in bset.files_exclude:
							continue
						if fullpath == bset.dest:
							ui.statuswin.addmsg(_("NOTE: Destination directory inside backup set. Omitting."))
						elif os.path.islink(fullpath):
							count += 1
						elif os.access(fullpath, os.R_OK):
							count += 1
					for d in dirs:
						fullpath = os.path.join(dirname, d)
						if fullpath in bset.files_exclude:
							dirs.remove(d)
							continue
						if os.access(fullpath, os.R_OK|os.X_OK):
							count += 1
					self.report_progress("%s: %d" % (_("Files found"), count))
			elif os.access(path, os.R_OK):
				count += 1

		self.report_progress(_("Backup source analysis complete."))
		return count

	def do_backup(self, backupset, ui, remote=False):
		"""
		Run a local backup of the given backup set.
		"""
		filecount = self.__analyze_source(backupset, ui)
		self.report_progress(_("Running backup"))
		stdout = LogHandler(ui.statuswin, ui.widgets, filecount, True)
		stderr = LogHandler(ui.statuswin)
		self.progress = 0
		self.report_progress(_("Creating backup"))

		try:
			rdiff_interface.BackupSet(
					backupset,
					self.destination,
					stdout,
					stderr,
					copy_set_file = not remote,
					is_ssh = remote,
					force = self.force)
		except rdiff_interface.RdiffError, e:
			if e.status != 0:
				raise BackupError(_("Backup failed: %s") % str(e))
		except:
			raise
		else:
			self.progress = 100
			self.report_progress(_("Backup complete"))
		finally:
			sys.stdout = sys.__stdout__
			sys.stderr = sys.__stderr__



class CDBackup(Backup):
	"""
	Provides methods for backing up files to a CD or DVD.
	"""
	def __init__(self, tmpdir='/tmp'):
		"""
		Initialise a CDBackup object.
		"""
		Backup.__init__(self)
		self.destination = os.path.join(tmpdir, "%s.cdimage" %
				version.APPPATH)
		self.isopath = os.path.join(tmpdir, "%s.iso" % version.APPPATH)
		gobject.threads_init()

	def check_destination(self):
		"""
		Clear the temporary directory before checking it.
		"""
		try:
			shutil.rmtree(self.destination)
		except:
			pass # Didn't exist in the first place

		Backup.check_destination(self)
	
	def show_iso_progress(self, progress):
		"""
		Helper function for reporting iso image creation progress.
		"""
		self.progress = progress
		self.report_progress(_("Creating CD image"))

	def create_iso(self, backupset, ui):
		"""
		Create an iso image using the Mkisofs class.
		"""
		self.report_progress(_("Creating temporary backup"))
		self.do_backup(backupset, ui)
		isomaker = mkisofs.Mkisofs()
		isomaker.set_progress_hook(self.show_iso_progress)
		isomaker.create_iso(self.destination, self.isopath)
		isoret = isomaker.get_retval()
		if isoret != 0:
			errmsg = os.strerror(isoret)
			msg = _("Backup failed; could not create CD image %(filename)s: %(error)s\n") %\
					{'filename':self.isopath, 'error':errmsg}
			raise BackupError(msg)
	
	def burn_iso(self, drive, cd_progress_cb):
		"""
		Burn the iso image to CD/DVD.
		"""
		self.report_progress(_("Writing image to CD/DVD"))

		track = braseroburn.TrackImageCfg()
		track.set_source(self.isopath)

		session = braseroburn.SessionCfg()
		session.add_track(track)
		session.set_burner(drive)

		options = braseroburn.BurnOptions(session)
		err = options.run()
		options.destroy()
		if err != gtk.RESPONSE_OK:
			self.progress = 0
			self.report_progress("")
			raise BackupError(_("An error occurred while burning the CD."))
			
		cdburner = braseroburn.BurnDialog()
		cdburner.show()
		if not cdburner.run(session):
			cdburner.destroy()
			self.progress = 0
			self.report_progress("")
			raise BackupError(_("An error occurred while burning the CD."))

		cdburner.destroy()
		
		self.report_progress(_("Cleaning up temporary files"))
		try:
			shutil.rmtree(dest_path)
			os.unlink(self.isopath)
		except:
			pass

		self.progress = 100
		self.report_progress(_("Backup complete"))

class RemoteBackup(Backup):
	"""
	Provides methods for backing up files to a remote server.
	"""

	def set_destination(self, user, path, host):
		"""
		For remote backup, the destination must include a username, a
		remote path and a hostname.
		"""
                error_string = ""
                if not user:
                        error_string += _("\nUser")
                if not host:
                        error_string += _("\nHost")
                if not path:
                        error_string += _("\nPath")
                if error_string:
                        raise DestinationError(DestinationError.FAIL_MISC, "",
					_("Missing fields:%s") % error_string)

		self.destination = "%s@%s::%s" % (user, host, path)
		self.user = user
		self.host = host
		self.path = path


	def do_remote_backup(self, backupset, ui):
		"""
		Do a remote backup.
		"""
		self.do_backup(backupset, ui, remote = True)
		try:
			inifile = os.path.join(rdiff_interface.setspath,
					backupset.path, "set.ini")
			setfile = os.path.join(self.path, "rdiff-backup-data",
					"%s.set" % version.APPPATH)
			args = "scp %s %s@%s:%s" % (inifile, self.user, self.host, setfile)
			scp = subprocess.Popen(args, shell=True)
			while scp.poll() is None:
				self.report_progress(_("Transferring backup set data"))
			if scp.poll() != 0:
				ui.dialogs.showmsg(
_("Backup completed, but could not copy the backup set data file. You can "
  "manually copy this file from\n%(source)s\n to\n%(filepath)s (on host "
  "%(hostname)s)") % {'source':inifile, 'filepath':setfile, 'hostname':self.host})

			self.progress = 100
			self.report_progress(_("Backup completed"))
		except Exception, e:
			raise BackupError(
				_("An error occurred while transferring '%s'.") %\
				inifile)

