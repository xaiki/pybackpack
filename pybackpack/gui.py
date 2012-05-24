from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import GdkPixbuf

import sys
import os
import shutil
import re
try:
	import braseromedia
except ImportError:
	pass

import rdiff_interface
import version
import dialogs
import actions
from LogHandler import LogHandler
from Copy import RecursiveCopy, RecursiveCount
from seteditor import SetEditor
from filechooser import FileChooser
from statuswindow import StatusWindow

class Gui:
	def __init__(self, backupsets):
		self.tmpdir = "/tmp"

                path = os.path.dirname(__file__)
                if path:
                    path += "/"

                self.builder = Gtk.Builder()
                builder.add_from_file(path + "gui.ui")

		self.win_main = self.builder.get_object("window_main")

		self.widgets.signal_autoconnect(self)
		self.builder.get_object('set_destination').set_model(
		    Gtk.ListStore(GObject.TYPE_STRING))
		self.builder.get_object('restore_src').set_model(Gtk.ListStore(GObject.TYPE_STRING))

		self.backupsets = backupsets
		self.backupsets.add_change_hook(self.refresh_set_list)
		self.seteditor = SetEditor(self.backupsets)
		self.statuswin = StatusWindow()
		self.dialogs = dialogs.Dialogs(self.win_main)

		self.setstore = Gtk.ListStore(
				GdkPixbuf.Pixbuf,		# Icon
				GObject.TYPE_STRING,	# Set name
				GObject.TYPE_PYOBJECT)  # The backup set

		renderer = Gtk.CellRendererPixbuf()
		renderer.set_property('xalign', 0.0)
		combo = self.builder.get_object('combo_backup_sets')
		combo.pack_start(renderer, False)
		combo.add_attribute(renderer, 'pixbuf', 0)

		renderer = Gtk.CellRendererText()
		renderer.set_property('xalign', 0.0)
		combo.pack_start(renderer, True)
		combo.add_attribute(renderer, 'text', 1)

		combo.set_model(self.setstore)
		self.newset = [combo.render_icon(Gtk.STOCK_NEW, Gtk.IconSize.MENU),
				_("New backup set"), None]
		self.refresh_set_list()
		combo.set_active(0)

		# other widget initialisation
		self.win_main.set_title(_("File Backup Manager"))
		self.builder.get_object('cmb_backup_type').set_active(0)
		self.builder.get_object('notebook3').set_current_page(0)
		self.__find_cd_burners()

	def add_prev_dest(self, dest):

		"""Add a previously used destination to the destination combo box."""

		self.builder.get_object('set_destination').get_model().append((dest,))

	def add_prev_restore_loc(self, loc):

		"""Add a previously used restore-from location."""

		self.builder.get_object('restore_src').get_model().append((loc,))

	##########################
	## MAIN WINDOW HANDLERS ##
	##########################

	### HOME PAGE ###
	def on_button_home_dir_backup_clicked(self, unused):
		self.select_set("home")
		self.builder.get_object('cmb_backup_type').set_active(1) # CDRW
		self.builder.get_object('notebook1').set_current_page(1) # backup page
		Gtk.main_iteration()
		self.builder.get_object('button_do_backup').emit("clicked")

	### BACKUP PAGE ###
	def on_combo_backup_sets_changed(self, widget):
		combo = self.builder.get_object('combo_backup_sets')
		active = combo.get_active()
		if active < 0:
			return
		selected = self.setstore[active][2]
		if selected is None:
			self.builder.get_object('label_backup_set_info').set_text(_("Edit a new backup set"))
			self.builder.get_object('frame_dest').set_sensitive(False)
			self.builder.get_object('button_delete_set').set_sensitive(False)
			return
		else:
			self.builder.get_object('label_backup_set_info').set_text(selected.desc)
		for widget in [	'backup_ssh_user', \
						'backup_ssh_host', \
						'backup_ssh_path']:
			self.builder.get_object(widget).set_text('')
		self.builder.get_object('set_destination').child.set_text('')
		if selected.dest[:7] == "sftp://":
			p = re.compile("sftp://([^@]+)@([^/]+)(.*)")
			matches = p.match(selected.dest)
			if len(matches.groups()) < 3:
				user = ""
				host = ""
				path = ""
			else:
				user = matches.group(1)
				host = matches.group(2)
				path = matches.group(3)
			self.builder.get_object('cmb_backup_type').set_active(2)
			self.builder.get_object('backup_ssh_user').set_text(user)
			self.builder.get_object('backup_ssh_host').set_text(host)
			self.builder.get_object('backup_ssh_path').set_text(path)
			self.builder.get_object('button_do_backup').set_sensitive(True)
		elif selected.dest[:7] == "cdrw://":
			device = selected.dest.replace("cdrw://", "")
			self.builder.get_object('cmb_backup_type').set_active(1)
			for row in self.drive_sel.get_model():
				if row[0] and row[0].get_device() == device:
					self.drive_sel.set_active_iter(row.iter)
			self.builder.get_object('button_do_backup').set_sensitive(True)
		else:
			if selected.removable:
				self.builder.get_object('backup_removable').set_active(True)
			else:
				self.builder.get_object('backup_removable').set_active(False)
			self.builder.get_object('cmb_backup_type').set_active(0)
			self.builder.get_object('set_destination').child.set_text(selected.dest)
		self.builder.get_object('frame_dest').set_sensitive(True)
		self.builder.get_object('button_delete_set').set_sensitive(True)

	def on_button_delete_set_clicked(self, unused):
		tree, itera = self.builder.get_object('combo_backup_sets').get_selection().get_selected()
		bset = tree.get_value(itera, 2)
		if bset.name == _("home"):
			self.dialogs.showerror(_("You cannot delete this set."))
			return True

		dlg = Gtk.MessageDialog(self.win_main,
                                        Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING,
                                        Gtk.ButtonsType.YES_NO,
			_("Are you sure you wish to delete the backup set '%s'?\n"
                          "Deleting this backup set will not delete any previous backups, "
                          "nor will it affect your ability to restore them.") % bset.name)

		dlg.connect("response", self.on_delete_set_dialog_response, bset)
		dlg.show()

	def on_delete_set_dialog_response(self, widget, response, set):
		if response ==Gtk.ResponseType.YES:
			set.delete()
			self.backupsets.remove(set)
			self.builder.get_object('backup_controls').set_sensitive(False)
			self.builder.get_object('button_delete_set').set_sensitive(False)
			if self.backupsets.count() == 0:
				self.builder.get_object('label_backup_set_info').set_text(
                                _("There are no remaining backup sets.\nTo create a new backup set, click 'New'."))
			else:
				self.builder.get_object('label_backup_set_info').set_text(
                                _("Select a backup set from the list on the left."))
			widget.destroy()
		else:
			widget.destroy()

	def on_set_destination_changed(self, widget):
		if len(widget.child.get_text()) > 0:
			self.builder.get_object('button_do_backup').set_sensitive(True)
		else:
			self.builder.get_object('button_do_backup').set_sensitive(False)

	def on_edit1_clicked(self, unused):
		combo = self.builder.get_object('combo_backup_sets')
		active = combo.get_active()
		if active > -1:
			selection = self.setstore[active]
			bset = selection[2]
			self.seteditor.setexitnotify(self.refresh_set_list)
			if self.seteditor.set_backupset_to_edit(bset):
				self.seteditor.show()
			else:
				self.dialogs.showerror(_("Selected backup set cannot be edited."))

	def on_button_do_backup_clicked(self, unused):
		rdiff_interface.Refresh()
		if self.builder.get_object('chk_show_output_log').get_active():
			self.statuswin.show()
		self.builder.get_object('notebook1').set_sensitive(False)
		self.builder.get_object('menubar1').set_sensitive(False)
		self.win_main.window.set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))
		while Gtk.events_pending():
			Gtk.main_iteration()
		try:
			if self.builder.get_object('cmb_backup_type').get_active() == 0: # local
				self.do_local_backup()
			elif self.builder.get_object('cmb_backup_type').get_active() == 1: # cdr
				self.do_cdr_backup()
			elif self.builder.get_object('cmb_backup_type').get_active() == 2: # ssh
				self.do_ssh_backup()
		finally:
			self.builder.get_object('notebook1').set_sensitive(True)
			self.builder.get_object('menubar1').set_sensitive(True)
			self.win_main.window.set_cursor(None)

	def show_progress(self, progress=0, status=None, unused=None):
		if status is not None:
			self.builder.get_object('progressbar1').set_text(status)
		else:
			self.builder.get_object('progressbar1').set_text("")

		if progress < 0:
			self.builder.get_object('progressbar1').pulse()
		else:
			self.builder.get_object('progressbar1').set_fraction(progress/100)
		Gtk.main_iteration()

	def on_cdburn_progress_changed(self, _, fract, unused):
		"""
		Wrapper callback for the CD burner progress signal.
		"""
		if fract > 0:
			self.show_progress(fract*100, _("Burning CD/DVD"))
		else:
			self.show_progress(0, _("Waiting for CD/DVD"))

	def do_cdr_backup(self):
		"""
		Kick off a backup to a CD/DVD
		"""
		active = self.builder.get_object('combo_backup_sets').get_active()
		bset = self.setstore[active][2]
		self.statuswin.addmsg(_("Starting backup of '%s' to CD\n") % bset.name)

		if self.drive_sel.get_active() == -1:
			self.dialogs.showerror(_("No CD burners detected."))
			self.statuswin.addmsg(_("Backup failed; no CD burners detected.\n"))
			return

		burner = self.drive_sel.get_active()

		self.__lock()

		bup = actions.CDBackup(self.tmpdir)
		bup.add_progress_cb(self.show_progress)
		try:
			bup.check_destination()
		except actions.DestinationError, d:
			if d.code != d.WARN_NEMPTY:
				self.dialogs.showerror(str(d))
				self.statuswin.addmsg(str(d))
				self.__unlock()
				return
			msg = _("The destination directory is not empty and it doesn't look like a previous backup. Continue?")
			if not self.__warn_and_confirm(msg):
				self.__unlock()
				return
			bup.force = True

		try:
			bup.create_iso(bset, self)
		except actions.BackupError, b:
			self.dialogs.showerror(str(b))
			self.statuswin.addmsg(str(b))
			self.__unlock()
			return

		try:
			bup.burn_iso(burner, self.on_cdburn_progress_changed)
		except actions.BackupError, b:
			self.dialogs.showerror(str(b))
			self.statuswin.addmsg(str(b))
			self.__unlock()
			return

		self.__unlock()

	def __lock(self):
		"""
		Make widgets insensitive while backing up.
		"""
		self.builder.get_object('vbox2').set_sensitive(False)
		self.builder.get_object('menu_backup').set_sensitive(False)
		self.builder.get_object('menu_restore').set_sensitive(False)

	def __unlock(self):
		"""
		Make widgets sensitive after backing up.
		"""
		self.builder.get_object('vbox2').set_sensitive(True)
		self.builder.get_object('menu_backup').set_sensitive(True)
		self.builder.get_object('menu_restore').set_sensitive(True)

	def __warn_and_confirm(self, msg):
		"""
		Show a warning dialog with a message and Yes/No buttons.
		"""
		dlg = Gtk.MessageDialog(self.builder.get_object('window_main'), \
                                        Gtk.DialogFlags.MODAL, Gtk.MessageType.QUESTION, \
                                        Gtk.ButtonsType.YES_NO, \
                                        msg)
		answer = dlg.run()
		dlg.destroy()
		if answer ==Gtk.ResponseType.YES:
			return True
		return False


	def do_local_backup(self):
		"""
		Backup files to a local storage device.
		"""
		destcombo = self.builder.get_object('set_destination')
		destination_path = destcombo.child.get_text()

		active = self.builder.get_object('combo_backup_sets').get_active()
		bset = self.setstore[active][2]

		if len(destination_path) == 0:
			self.dialogs.showerror(_("Please select a location to back up to."))
			return True
		self.statuswin.addmsg(_("Starting backup of '%(backup)s' to '%(destination)s'\n") %
							{'backup':bset.name, 'destination':destination_path})
		self.show_progress(0, _("Starting backup"))
		if self.builder.get_object('backup_removable').get_active():
			self.dialogs.showinfo(_("Please connect and mount the device for '%s'") % destination_path)
			while self.dialogs.response == None:
				Gtk.main_iteration() # kill some time until the user clicks the button
			if self.dialogs.response ==Gtk.ResponseType.CANCEL:
				self.statuswin.addmsg(_("Backup cancelled by user.\n"))
				return

		self.__lock()

		bup = actions.Backup()
		bup.add_progress_cb(self.show_progress)
		bup.set_destination(destination_path)
		try:
			self.show_progress(-1, _("Checking destination directory"))
			bup.check_destination()
		except actions.DestinationError, d:
			if d.code != d.WARN_NEMPTY:
				self.dialogs.showerror(str(d))
				self.statuswin.addmsg(str(d))
				self.__unlock()
				return
			msg = _("The destination directory is not empty and it doesn't look like a previous backup. Continue?")
			if not self.__warn_and_confirm(msg):
				self.__unlock()
				return
			bup.force = True

		try:
			bup.do_backup(bset, self)
			self.statuswin.addmsg(_("Backup completed.\n"))
		except actions.BackupError, b:
			self.dialogs.showerror(str(b))
			self.statuswin.addmsg(str(b))
			self.__unlock()
			return

		gotit = False
		for path in destcombo.get_model():
			if path[0] == destcombo.child.get_text():
				gotit = True
				break
		if not gotit:
			destcombo.get_model().append((destcombo.child.get_text(),))

		self.__unlock()

	def do_ssh_backup(self):
		"""
		Backup files to a remote server.
		"""
		user = self.builder.get_object('backup_ssh_user').get_text()
		host = self.builder.get_object('backup_ssh_host').get_text()
		path = self.builder.get_object('backup_ssh_path').get_text()
		tree, itera = self.builder.get_object('combo_backup_sets').get_selection().get_selected()
		bset = tree.get_value(itera, 2)

		self.statuswin.addmsg(_("Starting backup of '%(backup)s' to '%(hostname)s'") %
								{'backup':bset.name, 'hostname':host})
		self.__lock()

		bup = actions.RemoteBackup()
		bup.add_progress_cb(self.show_progress)
		try:
			bup.set_destination(user, path, host)
		except actions.DestinationError, d:
			self.dialogs.showerror(str(d))
			self.__unlock()
			return

		try:
			bup.do_remote_backup(bset, self)
			self.statuswin.addmsg(_("Backup completed.\n"))
		except actions.BackupError, b:
			self.dialogs.showerror(str(b))
			self.statuswin.addmsg(str(b))
			self.__unlock()
			return

		self.__unlock()


	def on_backup_local_dest_button_clicked(self, unused):
		filechooser = FileChooser()
		filechooser.set_return_type(filechooser.RETURN_FILENAME)
		filechooser.set_exitnotify(self.filechosen_backup_dst)
		filechooser.set_title(_("Select a backup destination"))
		filechooser.show()

	def filechosen_backup_dst(self, filename):
		self.builder.get_object('set_destination').child.set_text(filename)

	def on_cmb_backup_type_changed(self, widget):
		try:
			self.builder.get_object('notebook3').set_current_page(widget.get_active())
		except:
			pass


	def on_button_ssh_path_clicked(self, unused):
		host = self.builder.get_object('backup_ssh_host').get_text()
		user = self.builder.get_object('backup_ssh_user').get_text()
		if len(host) == 0 or len(user) == 0:
			return True
		filechooser = FileChooser()
		filechooser.set_title(_("Select a default remote location to backup to"))
		filechooser.set_return_type(filechooser.RETURN_URI)
		filechooser.set_exitnotify(self.filechosen_new_set_ssh_path)
		filechooser.set_title(_("Select a default remote location to backup to."))
		filechooser.show()
		filechooser.set_current_folder_uri("sftp://%s@%s/" %(user, host))

	def filechosen_new_set_ssh_path(self, uri):
		host = self.builder.get_object('backup_ssh_host').get_text().replace(".", "\.")
		user = self.builder.get_object('backup_ssh_user').get_text()
		patt = re.compile("sftp:/[/]+%s@%s(.*)" % (user, host))
		match = patt.match(uri)
		if match and len(match.groups()) > 0:
			self.builder.get_object('backup_ssh_path').set_text(match.group(1))

	### RESTORE PAGE ###
	def on_restore_src_button_clicked(self, unused):
		filechooser = FileChooser()
		filechooser.set_return_type(filechooser.RETURN_URI)
		filechooser.set_exitnotify(self.filechosen_restore_src)
		filechooser.set_title(_("Select a location to restore from"))
		self.builder.get_object('notebook1').set_current_page(2)
		filechooser.show()

	def filechosen_restore_src(self, uri):
		self.builder.get_object('restore_src').child.set_text("")
		if uri[:7] == "sftp://":
			p = re.compile("sftp://([^@]+)@([^/]+)(.*)")
			matches = p.match(uri)
			if len(matches.groups()) < 3:
				user = ""
				host = ""
				path = ""
			else:
				user = matches.group(1)
				host = matches.group(2)
				path = matches.group(3)
			self.builder.get_object('radio_restore_ssh').set_active(True)
			self.builder.get_object('restore_src').child.set_text(path)
			self.builder.get_object('restore_ssh_user').set_text(user)
			self.builder.get_object('restore_ssh_host').set_text(host)
		elif uri[:7] == "file://":
			self.builder.get_object('radio_restore_local').set_active(True)
			self.builder.get_object('restore_src').child.set_text(uri[7:])
			self.builder.get_object('restore_ssh_user').set_text("username")
			self.builder.get_object('restore_ssh_host').set_text("host")
		else:
			# TODO: no need to use a dialog here
			self.dialogs.showerror(_("Only sftp:// and file:// locations are supported."))

	def on_restore_src_changed(self, widget):
		if self.builder.get_object('radio_restore_ssh').get_active():
			self.builder.get_object('lbl_restore_name').set_text(_("Click the 'refresh' button to read this backup set"))
			self.builder.get_object('lbl_restore_target').set_text('')
			self.builder.get_object('lbl_restore_desc').set_text('')
			self.builder.get_object('button_do_restore').set_sensitive(False)
			self.builder.get_object('cmb_restore_increment').get_model().clear()
			return True
		widget.child.set_text(widget.child.get_text().replace("/rdiff-backup-data", ""))
		bset = rdiff_interface.ParseRestoreSrc(widget.child.get_text())
		if bset is not None:
			self.builder.get_object('button_do_restore').set_sensitive(True)
			self.builder.get_object('lbl_restore_target').set_text(_("This data will be restored to %s") % os.path.join(os.environ['HOME'], "restored_files", bset['name']))
			self.builder.get_object('lbl_restore_name').set_text(bset['name'])
			self.builder.get_object('lbl_restore_desc').set_text(bset['desc'])
			self.builder.get_object('cmb_restore_increment').set_model(bset['increments'])
			self.builder.get_object('cmb_restore_increment').set_active(0)
			if bset.has_key('readonly'):
				#self.builder.get_object('read_only_source').show()
				self.read_only_source = True
			else:
				#self.builder.get_object('read_only_source').hide()
				self.read_only_source = False
		else:
			self.builder.get_object('lbl_restore_target').set_text('')
			self.builder.get_object('lbl_restore_name').set_text('')
			self.builder.get_object('lbl_restore_desc').set_text('')
			self.builder.get_object('button_do_restore').set_sensitive(False)
			self.builder.get_object('cmb_restore_increment').set_model(Gtk.ListStore(GObject.TYPE_STRING))
			#self.builder.get_object('read_only_source').hide()
			self.read_only_source = False

	def on_button_do_restore_clicked(self, unused):
		restore_failed = False
		ssh_restore = self.builder.get_object('radio_restore_ssh').get_active()
		if ssh_restore:
			user = self.builder.get_object('restore_ssh_user').get_text()
			host = self.builder.get_object('restore_ssh_host').get_text()
			path = self.builder.get_object('restore_src').child.get_text()
			restore_source = "%s@%s::%s" % (user, host, path)
		else:
			restore_source = self.builder.get_object('restore_src').child.get_text()
		self.statuswin.addmsg(_("Starting restore operation from '%s'\n") % restore_source)
		self.show_progress(0, _("Starting restore operation..."))
		if self.builder.get_object('chk_rst_show_output_log').get_active():
			self.statuswin.show()
		rdiff_interface.Refresh()
		destination_path = os.path.join(os.environ['HOME'], "restored_files", self.builder.get_object('lbl_restore_name').get_text())
		if not os.path.exists(destination_path):
			try:
				os.makedirs(destination_path, 0755)
			except:
				self.dialogs.showerror(_("An error occurred when trying to create '%s'.") % destination_path)
				self.statuswin.addmsg(_("Restore failed; could not create destination path '%s'\n") % destination_path)
				return True
		status, reason = rdiff_interface.CheckDestination(destination_path, False) # flag even if there's an rdiff-backup-data sub dir
		if not status:
			if reason == "no_permission":
				self.dialogs.showerror(_("You don't have permission to write to '%s'.\n") % destination_path)
			elif reason == "not_empty":
				dlg = Gtk.MessageDialog( \
					self.builder.get_object('window_main'), \
                                        Gtk.DialogFlags.MODAL, Gtk.MessageType.QUESTION, \
                                        Gtk.ButtonsType.YES_NO, \
					(_("There are already files in '%s'.") % destination_path) + "\n"
					+ _("If you restore your backup to this location, these files will be erased permanently.") + "\n\n"
					+ _("Are you sure you want to do this?"))
				dlg.connect("response", self.on_overwrite_dialog_response, destination_path, self.on_button_do_restore_clicked)
				dlg.show()
			return True
		# if we've reached this point, it's ok to do the restore
		self.show_progress(0.25, _("Checking restore source..."))
		if self.read_only_source:
			self.total_count = RecursiveCount(restore_source)
			self.current_count = 0
			dest_path = os.path.join(self.tmpdir, "%s.restore" % version.APPPATH)
			self.show_progress(0.33, _("Copying from CD..."))
			self.statuswin.addmsg(_("Copying from CD (%(count)d files) to %(destination)s.") %
										{'count':self.total_count, 'destination':dest_path})
			try:
				shutil.rmtree(dest_path)
			except:
				pass
			try:
				os.makedirs(dest_path)
				RecursiveCopy(restore_source, dest_path, self.on_recursive_copy_step)
			except:
				self.dialogs.showerror(
					_("Couldn't copy CD from '%(cdpath)s' to '%(destination)s'.\n"
					  "Please check there is enough disk space and try again.") %
					{'cdpath':restore_source, 'destination':dest_path})
				self.statuswin.addmsg(_("Restore failed; could not copy CD to temporary location.\n"))
				return True
			self.statuswin.addmsg(_("CD copy finished."))
		self.show_progress(0.5, _("Restoring files..."))
		self.builder.get_object('button_do_restore').set_sensitive(False)
		self.builder.get_object('menu_backup').set_sensitive(False)
		self.builder.get_object('menu_restore').set_sensitive(False)
		stdout = LogHandler(self.statuswin, None, 0, True)
		stderr = LogHandler(self.statuswin)
		increment = self.builder.get_object('cmb_restore_increment').get_model()[self.builder.get_object('cmb_restore_increment').get_active()][1]
		GLib.idle_add(self.statuswin.scroll)
		self.statuswin.addmsg(_("Restoring files."))
		while Gtk.events_pending():
			Gtk.main_iteration()
		try:
			rdiff_interface.RestoreSet(restore_source, destination_path, stdout, stderr, increment)
		except:
			sys.stdout = sys.__stdout__
			sys.stderr = sys.__stderr__
			if len(stderr) > 0:
				self.statuswin.addmsg(_("An error occurred whilst restoring from '%s'.") % restore_source)
				self.statuswin.show()
				restore_failed = True
		if self.read_only_source:
			self.show_progress(0.75, _("Cleaning up %s...") % dest_path)
			self.statuswin.addmsg(_("Cleaning up temporary files from %s.") % dest_path)
			try:
				shutil.rmtree(dest_path)
			except:
				self.statuswin.addmsg(_("Cleaning up temporary files failed, please manually delete %s") % dest_path)
		self.builder.get_object('progressbar1').set_fraction(0)
		if not restore_failed:
			self.statuswin.addmsg(_("Restore succeeded.\n"))
			self.dialogs.showmsg(
				_("Restore succeeded.\nThe restored files are in 'restored_files/%s' in your home directory.") %
				self.builder.get_object('lbl_restore_name').get_text())
			if not ssh_restore:
				gotit = False
				for path in self.builder.get_object('restore_src').get_model():
					if path[0] == self.builder.get_object('restore_src').child.get_text():
						gotit = True
						break
				if not gotit:
					self.builder.get_object('restore_src').get_model().append((self.builder.get_object('restore_src').child.get_text(),))
		self.builder.get_object('button_do_restore').set_sensitive(True)
		self.builder.get_object('menu_backup').set_sensitive(True)
		self.builder.get_object('menu_restore').set_sensitive(True)

	def on_radio_restore_ssh_toggled(self, widget):
		if widget.get_active():
			self.builder.get_object('restore_ssh_user').set_sensitive(True)
			self.builder.get_object('restore_ssh_host').set_sensitive(True)
			self.builder.get_object('restore_ssh_refresh').set_sensitive(True)
		else:
			self.builder.get_object('restore_ssh_user').set_sensitive(False)
			self.builder.get_object('restore_ssh_host').set_sensitive(False)
			self.builder.get_object('restore_ssh_refresh').set_sensitive(False)

	def on_restore_ssh_refresh_clicked(self, unused):
		user = self.builder.get_object('restore_ssh_user').get_text()
		host = self.builder.get_object('restore_ssh_host').get_text()
		path = self.builder.get_object('restore_src').child.get_text()
		bset = rdiff_interface.ParseRestoreSSHSrc(user, host, path)
		if bset is not None:
			self.builder.get_object('button_do_restore').set_sensitive(True)
			self.builder.get_object('lbl_restore_target').set_text(_("This data will be restored to %s") %
						os.path.join(os.environ['HOME'], "restored_files", bset['name']))
			self.builder.get_object('lbl_restore_name').set_text(bset['name'])
			self.builder.get_object('lbl_restore_desc').set_text(bset['desc'])
			self.builder.get_object('cmb_restore_increment').set_model(bset['increments'])
			self.builder.get_object('cmb_restore_increment').set_active(0)
			if bset.has_key('readonly'):
				#self.builder.get_object('read_only_source').show()
				self.read_only_source = True
			else:
				#self.builder.get_object('read_only_source').hide()
				self.read_only_source = False
		else:
			self.dialogs.showerror(_("An error occurred while reading the remote backup set information.\n"
					"Please check the username, host name and path that you have entered and try again."))
			self.builder.get_object('lbl_restore_target').set_text('')
			self.builder.get_object('lbl_restore_name').set_text('')
			self.builder.get_object('lbl_restore_desc').set_text('')
			self.builder.get_object('button_do_restore').set_sensitive(False)
			self.builder.get_object('cmb_restore_increment').get_model().clear()

	##########################
	##     MENU HANDLERS    ##
	##########################
	def on_about1_activate(self, unused):
		logo = None
		logofile = 'pybackpack_logo.png'
		for d in [os.path.dirname(__file__), '/usr/share/pixmaps']:
			if os.path.exists(os.path.join(d,logofile)):
				logo = GdkPixbuf.Pixbuf.new_from_file(os.path.join(d, logofile))
				break
		about = _("%s is a tool for backing up user data for the GNOME Desktop") % version.APPNAME
		dlg = Gtk.AboutDialog()
		dlg.set_name(version.APPNAME)
		dlg.set_version(version.VERSION)
		dlg.set_copyright(version.COPYRIGHT)
		dlg.set_license(version.LICENSE)
		dlg.set_wrap_license(True)
		dlg.set_website(version.WEBSITE)
		dlg.set_authors(version.AUTHORS)
		dlg.set_logo(logo)
		dlg.run()
		dlg.destroy()

	def on_view_output_log_activate(self, unused):
		self.statuswin.show()

	##########################
	##     MISC HANDLERS    ##
	##########################
	def on_recursive_copy_step(self, file):
		self.current_count += 1.0
		self.show_progress((self.current_count/self.total_count) * 100,
				_("Copying from CD:") + "%s" % os.path.basename(file))
		Gtk.main_iteration()

	def on_overwrite_dialog_response(self, widget, response, path, func):
		if response ==Gtk.ResponseType.YES:
			# user is totally sure they want to delete, so let's do it
			widget.destroy()
			try:
				shutil.rmtree(path)
			except OSError, e:
				self.dialogs.showerror(
					_("Could not remove '%(filename)s': "
					  "%(error_msg)s") %\
						{'filename': e.filename,
						'error_msg': e.strerror})
				self.statuswin.addmsg(_("Operation failed.\n"))
				return

			func(None) # go back to where we came from
		else:
			self.statuswin.addmsg(_("Restore aborted, no files were changed.\n"))
			widget.destroy()

	def __find_cd_burners(self):
		"""
		Detect CD burners and populate comboboxes
		"""
		sel = None
		try:
			sel = braseromedia.DriveSelection()
		except NameError:
			return False

		self.builder.get_object('vbox_burners').add(sel)
		sel.show()
		self.drive_sel = sel
		return True

	def refresh_set_list(self, selected=None):
		combo = self.builder.get_object('combo_backup_sets')
		self.setstore.clear()
		self.setstore.append(self.newset)
		for bset in self.backupsets:
			if bset.dest[:7] == "sftp://":
				set_type = Gtk.STOCK_NETWORK
			elif bset.dest[:7] == "cdrw://":
				set_type = Gtk.STOCK_CDROM
			else:
				set_type = Gtk.STOCK_DIRECTORY
			self.setstore.append( [combo.render_icon(set_type,
				Gtk.ICON_SIZE_MENU), bset.name, bset])
		if selected is not None:
			self.select_set(selected.name)
		else:
			self.builder.get_object('button_do_backup').set_sensitive(False)


	def select_set(self, setname):
		"""Iterates through the set list and places the sets treeview cursor
				on the given set"""
		combo = self.builder.get_object('combo_backup_sets')
		for row in self.setstore:
			if row[1] == setname:
				combo.set_active_iter(row.iter)
				break

	def gtk_main_quit(self, unused):

		""" Write the backup and restore MRUs back to disk """

		for mru, store in [("backup_mru", self.builder.get_object('set_destination').get_model()),\
			("restore_mru", self.builder.get_object('restore_src').get_model())]:
			outfile = open(os.path.join(
				os.environ['HOME'],
				".%s" % version.APPPATH,
				mru), "w")
			for line in store:
				outfile.write("%s\n" % line[0])
			outfile.close()

		Gtk.main_quit()
