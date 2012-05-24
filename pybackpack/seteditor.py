from gi.repository import Gtk
from gi.repository import GdkPixbuf

import os
import re

try:
        import braseromedia
except ImportError:
        pass

import backupsets
import dialogs
from filechooser import FileChooser

class SetEditor:
    def __init__(self, bupsets):
        self.exitnotify = None
        self.backupsets = bupsets
        self.includes = {}
        self.excludes = {}

        path = os.path.dirname(__file__)
        if path:
            path += "/"

        try:
            self.builder = Gtk.Builder()
            self.builder.add_from_file(path + "mdt.ui")
        except RuntimeError:
            dlg = Gtk.MessageDialog(None,  Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
                                    Gtk.ButtonsType.CLOSE,
                                    _("Unable to start the backup set editor"))
            dlg.connect("response", lambda w: Gtk.main_quit())

        # Connect signals to handler functions
        self.builder.connect_signals(self)
        self.filelist = Gtk.ListStore(GdkPixbuf.Pixbuf, GdkPixbuf.Pixbuf, str , bool)
        self.builder.get_object('treeview_excluded').set_model(self.filelist)
        self.builder.get_object('treeview_excluded1').set_model(self.filelist)
        self.builder.get_object('treeview_summary').set_model(self.filelist)

        self.dialogs = dialogs.Dialogs(self.builder.get_object('window_new_set'))

        # List layout: Include/Exclude icon,
        #              file/folder icon,
        #              path,
        #              include(True)/exclude(False)

        # Add the Path column to the treeview
        self.builder.get_object('treeview_excluded').append_column(self._new_column())
        self.builder.get_object('treeview_excluded1').append_column(self._new_column())
        self.builder.get_object('treeview_summary').append_column(self._new_column())

        self.builder.get_object('comboboxtext1').set_active(2)

        self.builder.get_object('filechooserwidget1').set_current_folder(os.environ['HOME'])
#        self.builder.get_object('cmb_dst_type').set_active(0)
#        self.builder.get_object('notebook').set_current_page(0)

        self.drive_sel = None
        self.find_cd_burners()

    def _new_column(self):
        column = Gtk.TreeViewColumn()
#        column.set_title(_("Path"))
        column.set_spacing(3)
        renderer = Gtk.CellRendererPixbuf()
        column.pack_start(renderer, expand=False)
        column.add_attribute(renderer, 'pixbuf', 0)
        renderer = Gtk.CellRendererPixbuf()
        column.pack_start(renderer, expand=False)
        column.add_attribute(renderer, 'pixbuf', 1)
        renderer = Gtk.CellRendererText()
        column.pack_start(renderer, expand=True)
        column.add_attribute(renderer, 'text', 2)
        return column

    def setexitnotify(self, func=None):

        """Set the callback that will be called when the set editor finishes"""

        self.exitnotify = func

    def mdt_show_prefs_cb (self, widget=None, event=None):
        self.builder.get_object('mdt_prefs').show()

    def mdt_show_file_chooser_cb (self, widget=None, event=None):
        self.builder.get_object('filechooserwidget1').show()

    def show(self):
        self.builder.get_object('mdt_main').show()
#        self.builder.get_object('mdt_prefs').show()
#        self.builder.get_object('druid_page_2').show()
#        self.builder.get_object('druid_page_start').show()
#        self.builder.get_object('druid_page_finish').show()
#        self.builder.get_object('window_new_set').show()


    def druid_cleanup(self, widget=None, event=None):

        """Resets the 'new backup set' druid to a 'clean' state"""

        self.builder.get_object('window_new_set').hide()
        self.builder.get_object('window_new_set').set_title(_("Create New Backup Set"))
        self.builder.get_object('druid1').set_page(self.builder.get_object('druid_page_start'))

        for widget in [ 'entry_new_set_name', \
                        'entry_new_set_desc', \
                        'entry_new_set_def_dest', \
                        'entry_ssh_user', \
                        'entry_ssh_host', \
                        'entry_ssh_path']:
            self.builder.get_object(widget).set_text('')
        self.builder.get_object('cmb_dst_type').set_active(0)
        self.builder.get_object('new_set_overwrite').set_active(False)
        self.builder.get_object('frame_set_exists_warning').hide()
        self.builder.get_object('frame_ssh_error').hide()
        self.builder.get_object('frame_empty_set_name_error').hide()
        self.builder.get_object('frame_cd_burner_error').hide()
        self.builder.get_object('entry_new_set_name').set_sensitive(True)

        self.builder.get_object('filechooserwidget1').set_current_folder(os.environ['HOME'])
        self.builder.get_object('druidfilelist_label').set_text(_("0 items"))
        self.filelist.clear()

        return True

    def set_backupset_to_edit(self, buset):

        """
        Initialises the input widgets in the backup set editor to the
        settings defined in an existing set. Special case is the 'home'
        set which cannot be edited by the user.

        Arguments:
                buset - The backup set.

        Returns:
                True if successful (buset is not 'home' or invalid)
                False otherwise
        """

        druidfilelist = self.builder.get_object('treeview_excluded')
        if buset is not None:
            if buset.name == _('home'):
                return False

            self.builder.get_object('entry_new_set_name').set_text(buset.name)
            self.builder.get_object('entry_new_set_name').set_sensitive(False)
            self.builder.get_object('entry_new_set_desc').set_text(buset.desc)

            if buset.dest[:7] == "sftp://":
                p = re.compile("sftp://([^@]+)@([^/]+)(.*)")
                matches = p.match(buset.dest)
                if len(matches.groups()) < 3:
                    user = ""
                    host = ""
                    path = ""
                else:
                    user = matches.group(1)
                    host = matches.group(2)
                    path = matches.group(3)
                self.builder.get_object('cmb_dst_type').set_active(2)
                self.builder.get_object('entry_ssh_user').set_text(user)
                self.builder.get_object('entry_ssh_host').set_text(host)
                self.builder.get_object('entry_ssh_path').set_text(path)
            elif buset.dest[:7] == "cdrw://":
                self.builder.get_object('cmb_dst_type').set_active(1)
            else:
                self.builder.get_object('cmb_dst_type').set_active(0)
                self.builder.get_object('entry_new_set_def_dest').set_text(buset.dest)
            self.builder.get_object('new_set_overwrite').set_active(True)
            druidfilelistmodel = druidfilelist.get_model()
            for f in buset.files_exclude:
                if f == "**":
                    continue
                if os.path.isdir(f):
                    druidfilelistmodel.append([druidfilelist.render_icon(Gtk.STOCK_REMOVE,\
                        Gtk.IconSize.MENU, "TreeView"), druidfilelist.render_icon(\
                        Gtk.STOCK_DIRECTORY, Gtk.IconSize.MENU, "TreeView"), f, False])
                else:
                    druidfilelistmodel.append([druidfilelist.render_icon(Gtk.STOCK_REMOVE,\
                        Gtk.IconSize.MENU, "TreeView"), druidfilelist.render_icon(\
                        Gtk.STOCK_FILE, Gtk.IconSize.MENU, "TreeView"), f, False])
            for f in buset.files_include:
                if os.path.isdir(f):
                    druidfilelistmodel.append([druidfilelist.render_icon(Gtk.STOCK_ADD,\
                        Gtk.IconSize.MENU, "TreeView"), druidfilelist.render_icon(\
                        Gtk.STOCK_DIRECTORY, Gtk.IconSize.MENU, "TreeView"), f, True])
                else:
                    druidfilelistmodel.append([druidfilelist.render_icon(Gtk.STOCK_ADD,\
                        Gtk.IconSize.MENU, "TreeView"), druidfilelist.render_icon(\
                        Gtk.STOCK_FILE, Gtk.IconSize.MENU, "TreeView"), f, True])
            self.builder.get_object('window_new_set').set_title(_("Editing backup set '%s'") % buset.name)
            self.builder.get_object('druid1').set_page(self.builder.get_object('druid_page_2'))
        else:
            self.builder.get_object('entry_new_set_name').set_text("")
            self.builder.get_object('entry_new_set_desc').set_text("")
            self.builder.get_object('entry_new_set_name').set_sensitive(True)
            self.builder.get_object('window_new_set').set_title(_("Editing new backup set"))
            self.builder.get_object('druid1').set_page(self.builder.get_object('druid_page_start'))

        if len(druidfilelist)==1:
            self.builder.get_object('druidfilelist_label').set_text("1 item")
        else:
            self.builder.get_object('druidfilelist_label').set_text("%d items"%len(druidfilelist))
        self.builder.get_object('druid_page_start').show()
        self.builder.get_object('druid_page_finish').show()
        return True

    # Event handlers start here

    def on_entry_new_set_name_changed(self, widget):
        widget.set_text(widget.get_text().replace("/", ""))

    def on_cmb_dst_type_changed(self, widget):
        try:
            self.builder.get_object('notebook').set_current_page(widget.get_active())
        except:
            pass

    def on_druid_page_2_next(self, widget, event):

        """Check user input"""

        if len(self.builder.get_object('entry_new_set_name').get_text()) == 0:
            self.builder.get_object('frame_empty_set_name_error').show()
            return True
        else:
            self.builder.get_object('frame_empty_set_name_error').hide()

        newsetname = self.builder.get_object('entry_new_set_name').get_text()
        if self.backupsets.get_named_set(newsetname) is not None and \
                not self.builder.get_object('new_set_overwrite').get_active():
            self.builder.get_object('label_set_exists_warning').set_text(
                        _("A set with the name '%s' already exists.\n"
                        "You can either enter a new name in the text box "
                        "above, or overwrite the existing set.") % newsetname)
            self.builder.get_object('frame_set_exists_warning').show()
            return True
        else:
            self.builder.get_object('frame_set_exists_warning').hide()

        # ok, the set doesn't already exist - have a crack at compiling the default destination string
        if self.builder.get_object('cmb_dst_type').get_active() == 0: # local
            self.builder.get_object('druid_summary_dest').set_text(
                self.builder.get_object('entry_new_set_def_dest').get_text())

        elif self.builder.get_object('cmb_dst_type').get_active() == 2: # SSH
            host = self.builder.get_object('entry_ssh_host').get_text()
            user = self.builder.get_object('entry_ssh_user').get_text()
            path = self.builder.get_object('entry_ssh_path').get_text()
            if len(host) == 0 or len(user) == 0 or len(path) == 0 or path[0] != "/":
                self.builder.get_object('frame_ssh_error').show()
                return True
            else:
                self.builder.get_object('frame_ssh_error').hide()
            self.builder.get_object('druid_summary_dest').set_text("sftp://%s@%s%s" % (user, host, path))

        elif self.builder.get_object('cmb_dst_type').get_active() == 1: # CD burner
            if self.drive_sel is None:
                return True
            active = self.drive_sel.get_active()
            if active:
		    dest = active.get_block_device()
		    self.builder.get_object('druid_summary_dest').set_text("cdrw://%s" % dest)
		    self.builder.get_object('chk_removable_device').set_active(True)
        self.builder.get_object('druid_page_3').set_title(_("Add Files/Folders to '%s'") % self.builder.get_object('entry_new_set_name').get_text())
        self.builder.get_object('druid_summary_name').set_text(self.builder.get_object('entry_new_set_name').get_text())
        self.builder.get_object('druid_summary_desc').set_text(self.builder.get_object('entry_new_set_desc').get_text())

    def on_druid_page_3_next(self, widget, event):
        if len(self.filelist) == 0:
            self.dialogs.showerror(_("You cannot create an empty backup set."))
            return True

    def on_button_ssh_path_clicked(self, widget):
        host = self.builder.get_object('entry_ssh_host').get_text()
        user = self.builder.get_object('entry_ssh_user').get_text()
        if len(host) == 0 or len(user) == 0:
            return True
        filechooser = FileChooser()
        filechooser.set_return_type(filechooser.RETURN_URI)
        filechooser.set_exitnotify(self.filechosen_new_set_ssh_path)
        filechooser.set_title(_("Select a default remote location to backup to."))
        filechooser.show()
        filechooser.set_current_folder_uri("sftp://%s@%s/" %(user, host))

    def filechosen_new_set_ssh_path(self, uri):
        host = self.builder.get_object('entry_ssh_host').get_text().replace(".", "\.")
        user = self.builder.get_object('entry_ssh_user').get_text()
        patt = re.compile("sftp:/[/]+%s@%s(.*)" % (user, host))
        match = patt.match(uri)
        if len(match.groups()) > 0:
            self.builder.get_object('entry_ssh_path').set_text(match.group(1))

    def on_button_default_dest_clicked(self, widget):
        filechooser = FileChooser()
        filechooser.set_return_type(filechooser.RETURN_FILENAME)
        filechooser.set_exitnotify(self.filechosen_new_set_default_dest)
        filechooser.set_title(_("Select a default destination"))
        filechooser.show()

    def filechosen_new_set_default_dest(self, filename):
        self.builder.get_object('entry_new_set_def_dest').set_text(filename)

    def on_druid_page_finish_prepare(self, widget, event):
        event.set_buttons_sensitive(False, False, False, False)

    def on_druid_page_finish_finish(self, event, something):
        buset = self.backupsets.get_named_set(self.builder.get_object('druid_summary_name').get_text())
        if buset is None:
            buset = backupsets.BackupSet(self.backupsets.configpath)
        buset.name = self.builder.get_object('druid_summary_name').get_text()
        if not buset.path:
            buset.path = buset.name
        buset.desc = self.builder.get_object('druid_summary_desc').get_text()
        buset.dest = self.builder.get_object('druid_summary_dest').get_text()
        buset.removable = self.builder.get_object('chk_removable_device').get_active()
        buset.files_include = self.includes
        buset.files_exclude = self.excludes
        try:
            buset.write()
            if buset not in self.backupsets:
                self.backupsets.add(buset)
            if callable(self.exitnotify):
                self.exitnotify(buset)
            self.druid_cleanup()
        except OSError, e:
            self.builder.get_object('druid_page_finish').set_text(
                _("ERROR: Couldn't write new set %(name)s: %(error)s") %
                {'name':self.builder.get_object('entry_new_set_name').get_text(), 'error':e})

#    def filechooser_done_cb(self, widget):
#        self.builder.get_object('filechooserwidget1').hide()

    def prefs_done_cb(self, widget):
#        self.builder.get_object('filechooserwidget1').hidea()
        self.builder.get_object('mdt_prefs').hide()

    def filelist_remove (self, f):
        for p in self.filelist:
            if p[2] == f:
                i = self.filelist.iter_nth_child
                self.filelist.remove(p.iter)
                if self.excludes.has_key(f):
                    del self.excludes[f]
                elif self.includes.has_key(f):
                    del self.includes[f]
                return True
        return False

    def filelist_push (self, f, inc=True):
        widget = Gtk.Image()
        icon = []

        if os.path.isdir(f):
            icon.append(Gtk.STOCK_DIRECTORY)
        else:
            icon.append(Gtk.STOCK_FILE)

        if inc == True:
            if f in self.includes:
                return
            if f in self.excludes:
                self.filelist_remove (f)
            self.includes[f] = True
            icon.append(Gtk.STOCK_ADD)
        else:
            if f in self.excludes:
                return
            if f in self.includes:
                self.filelist_remove (f)
            self.excludes[f] = True
            icon.append(Gtk.STOCK_REMOVE)

        self.filelist.append([widget.render_icon(icon.pop(), Gtk.IconSize.LARGE_TOOLBAR, "TreeView"),
                              widget.render_icon(icon.pop(), Gtk.IconSize.DIALOG, "TreeView"),
                              f, True])

    def filelist_refresh_count (self):
        if len(self.filelist) == 1:
            self.builder.get_object('druidfilelist_label').set_text(_("1 item"))
        else:
            self.builder.get_object('druidfilelist_label').set_text(_("%d items")%len(self.filelist))

    def on_button_add_to_set_clicked(self, widget):
        for f in self.builder.get_object('filechooserwidget1').get_filenames():
            self.filelist_push (f, inc=True)
        self.filelist_refresh_count ()
#        self.builder.get_object('filechooserwidget1').unselect_all()

    def on_button_exc_from_set_clicked(self, widget):
        for f in self.builder.get_object('filechooserwidget1').get_filenames():
            self.filelist_push (f, inc=False)
        self.filelist_refresh_count ()

#        self.builder.get_object('filechooserwidget1').unselect_all()

    def on_button_remove_from_set_clicked(self, widget):
        selection = self.builder.get_object('treeview_excluded').get_selection()
        store, row = selection.get_selected()
        if row is not None:
            store.remove(row)
            if len(self.filelist)==1:
                self.builder.get_object('druidfilelist_label').set_text(_("1 item"))
            else:
                self.builder.get_object('druidfilelist_label').set_text(_("%d items")%len(self.filelist))
        else: # this is really hackish, how can we get a better behaviour ?
            for f in self.builder.get_object('filechooserwidget1').get_filenames():
                self.filelist_remove(f)


    def find_cd_burners(self):

        """ Populate a combo box with the names of available CD/DVD drives """
        try:
            braseromedia
        except NameError:
            error_string = _("No CD burners available, because you do not have the python module \
braseromedia.")
            self.builder.get_object('lbl_cd_burner').set_text(error_string)
        else:
            self.drive_sel = braseromedia.DriveSelection()
            self.builder.get_object('hbox30').add(self.drive_sel)
            self.drive_sel.show()

    def on_hiddenfiles_toggled(self, event):
        fc = self.builder.get_object('filechooserwidget1')
        fc.set_show_hidden(event.get_active())

if __name__ == "__main__":
    def _(m):
        return m

    s = SetEditor(backupsets.BackupSets(''))

    s.builder.get_object('mdt_main').connect ("destroy", lambda w: Gtk.main_quit())
    s.show()

    Gtk.main()
