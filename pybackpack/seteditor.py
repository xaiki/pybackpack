import os
import re
import gtk
import gtk.glade
import gobject
import gnome
import gnome.ui
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
        try:
            self.widgets = gtk.glade.XML("%s/seteditor.glade"
                           % os.path.dirname(__file__))
        except RuntimeError:
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,
                  gtk.BUTTONS_CLOSE,_("Unable to start the backup set editor"))
            dlg.connect("response", lambda w: gtk.main_quit())

        # Connect signals to handler functions
        self.widgets.signal_autoconnect(self)
        self.filelist = gtk.ListStore(gtk.gdk.Pixbuf, gtk.gdk.Pixbuf, gobject.TYPE_STRING, bool)

        self.widgets.get_widget('treeview_druidfilelist').set_model(self.filelist)
        self.widgets.get_widget('druid_summary_filelist').set_model(self.filelist)

        self.dialogs = dialogs.Dialogs(self.widgets.get_widget('window_new_set'))

        # List layout: Include/Exclude icon,
        #              file/folder icon,
        #              path,
        #              include(True)/exclude(False)

        # Add the Path column to the treeview
        self.widgets.get_widget('treeview_druidfilelist').append_column(self._new_column())
        self.widgets.get_widget('druid_summary_filelist').append_column(self._new_column())

        self.widgets.get_widget('filechooserwidget1').set_current_folder(os.environ['HOME'])
        self.widgets.get_widget('cmb_dst_type').set_active(0)
        self.widgets.get_widget('notebook').set_current_page(0)

        self.drive_sel = None
        self.find_cd_burners()

    def _new_column(self):
        column = gtk.TreeViewColumn()
        column.set_title(_("Path"))
        column.set_spacing(3)
        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, expand=False)
        column.add_attribute(renderer, 'pixbuf', 0)
        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, expand=False)
        column.add_attribute(renderer, 'pixbuf', 1)
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, expand=True)
        column.add_attribute(renderer, 'text', 2)
        return column

    def setexitnotify(self, func=None):

        """Set the callback that will be called when the set editor finishes"""

        self.exitnotify = func

    def show(self):
        self.widgets.get_widget('druid_page_start').show()
        self.widgets.get_widget('druid_page_finish').show()
        self.widgets.get_widget('window_new_set').show()


    def druid_cleanup(self, widget=None, event=None):

        """Resets the 'new backup set' druid to a 'clean' state"""

        self.widgets.get_widget('window_new_set').hide()
        self.widgets.get_widget('window_new_set').set_title(_("Create New Backup Set"))
        self.widgets.get_widget('druid1').set_page(self.widgets.get_widget('druid_page_start'))

        for widget in [ 'entry_new_set_name', \
                        'entry_new_set_desc', \
                        'entry_new_set_def_dest', \
                        'entry_ssh_user', \
                        'entry_ssh_host', \
                        'entry_ssh_path']:
            self.widgets.get_widget(widget).set_text('')
        self.widgets.get_widget('cmb_dst_type').set_active(0)
        self.widgets.get_widget('new_set_overwrite').set_active(False)
        self.widgets.get_widget('frame_set_exists_warning').hide()
        self.widgets.get_widget('frame_ssh_error').hide()
        self.widgets.get_widget('frame_empty_set_name_error').hide()
        self.widgets.get_widget('frame_cd_burner_error').hide()
        self.widgets.get_widget('entry_new_set_name').set_sensitive(True)

        self.widgets.get_widget('filechooserwidget1').set_current_folder(os.environ['HOME'])
        self.widgets.get_widget('druidfilelist_label').set_text(_("0 items"))
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

        druidfilelist = self.widgets.get_widget('treeview_druidfilelist')
        if buset is not None:
            if buset.name == _('home'):
                return False

            self.widgets.get_widget('entry_new_set_name').set_text(buset.name)
            self.widgets.get_widget('entry_new_set_name').set_sensitive(False)
            self.widgets.get_widget('entry_new_set_desc').set_text(buset.desc)

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
                self.widgets.get_widget('cmb_dst_type').set_active(2)
                self.widgets.get_widget('entry_ssh_user').set_text(user)
                self.widgets.get_widget('entry_ssh_host').set_text(host)
                self.widgets.get_widget('entry_ssh_path').set_text(path)
            elif buset.dest[:7] == "cdrw://":
                self.widgets.get_widget('cmb_dst_type').set_active(1)
            else:
                self.widgets.get_widget('cmb_dst_type').set_active(0)
                self.widgets.get_widget('entry_new_set_def_dest').set_text(buset.dest)
            self.widgets.get_widget('new_set_overwrite').set_active(True)
            druidfilelistmodel = druidfilelist.get_model()
            for f in buset.files_exclude:
                if f == "**":
                    continue
                if os.path.isdir(f):
                    druidfilelistmodel.append([druidfilelist.render_icon(gtk.STOCK_REMOVE,\
                        gtk.ICON_SIZE_MENU, "TreeView"), druidfilelist.render_icon(\
                        gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_MENU, "TreeView"), f, False])
                else:
                    druidfilelistmodel.append([druidfilelist.render_icon(gtk.STOCK_REMOVE,\
                        gtk.ICON_SIZE_MENU, "TreeView"), druidfilelist.render_icon(\
                        gtk.STOCK_FILE, gtk.ICON_SIZE_MENU, "TreeView"), f, False])
            for f in buset.files_include:
                if os.path.isdir(f):
                    druidfilelistmodel.append([druidfilelist.render_icon(gtk.STOCK_ADD,\
                        gtk.ICON_SIZE_MENU, "TreeView"), druidfilelist.render_icon(\
                        gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_MENU, "TreeView"), f, True])
                else:
                    druidfilelistmodel.append([druidfilelist.render_icon(gtk.STOCK_ADD,\
                        gtk.ICON_SIZE_MENU, "TreeView"), druidfilelist.render_icon(\
                        gtk.STOCK_FILE, gtk.ICON_SIZE_MENU, "TreeView"), f, True])
            self.widgets.get_widget('window_new_set').set_title(_("Editing backup set '%s'") % buset.name)
            self.widgets.get_widget('druid1').set_page(self.widgets.get_widget('druid_page_2'))
        else:
            self.widgets.get_widget('entry_new_set_name').set_text("")
            self.widgets.get_widget('entry_new_set_desc').set_text("")
            self.widgets.get_widget('entry_new_set_name').set_sensitive(True)
            self.widgets.get_widget('window_new_set').set_title(_("Editing new backup set"))
            self.widgets.get_widget('druid1').set_page(self.widgets.get_widget('druid_page_start'))

        if len(druidfilelist)==1:
            self.widgets.get_widget('druidfilelist_label').set_text("1 item")
        else:
            self.widgets.get_widget('druidfilelist_label').set_text("%d items"%len(druidfilelist))
        self.widgets.get_widget('druid_page_start').show()
        self.widgets.get_widget('druid_page_finish').show()
        return True

    # Event handlers start here

    def on_entry_new_set_name_changed(self, widget):
        widget.set_text(widget.get_text().replace("/", ""))

    def on_cmb_dst_type_changed(self, widget):
        try:
            self.widgets.get_widget('notebook').set_current_page(widget.get_active())
        except:
            pass

    def on_druid_page_2_next(self, widget, event):

        """Check user input"""

        if len(self.widgets.get_widget('entry_new_set_name').get_text()) == 0:
            self.widgets.get_widget('frame_empty_set_name_error').show()
            return True
        else:
            self.widgets.get_widget('frame_empty_set_name_error').hide()

        newsetname = self.widgets.get_widget('entry_new_set_name').get_text()
        if self.backupsets.get_named_set(newsetname) is not None and \
                not self.widgets.get_widget('new_set_overwrite').get_active():
            self.widgets.get_widget('label_set_exists_warning').set_text(
                        _("A set with the name '%s' already exists.\n"
                        "You can either enter a new name in the text box "
                        "above, or overwrite the existing set.") % newsetname)
            self.widgets.get_widget('frame_set_exists_warning').show()
            return True
        else:
            self.widgets.get_widget('frame_set_exists_warning').hide()

        # ok, the set doesn't already exist - have a crack at compiling the default destination string
        if self.widgets.get_widget('cmb_dst_type').get_active() == 0: # local
            self.widgets.get_widget('druid_summary_dest').set_text(
                self.widgets.get_widget('entry_new_set_def_dest').get_text())

        elif self.widgets.get_widget('cmb_dst_type').get_active() == 2: # SSH
            host = self.widgets.get_widget('entry_ssh_host').get_text()
            user = self.widgets.get_widget('entry_ssh_user').get_text()
            path = self.widgets.get_widget('entry_ssh_path').get_text()
            if len(host) == 0 or len(user) == 0 or len(path) == 0 or path[0] != "/":
                self.widgets.get_widget('frame_ssh_error').show()
                return True
            else:
                self.widgets.get_widget('frame_ssh_error').hide()
            self.widgets.get_widget('druid_summary_dest').set_text("sftp://%s@%s%s" % (user, host, path))

        elif self.widgets.get_widget('cmb_dst_type').get_active() == 1: # CD burner
            if self.drive_sel is None:
                return True
            active = self.drive_sel.get_active()
            if active:
		    dest = active.get_block_device()
		    self.widgets.get_widget('druid_summary_dest').set_text("cdrw://%s" % dest)
		    self.widgets.get_widget('chk_removable_device').set_active(True)
        self.widgets.get_widget('druid_page_3').set_title(_("Add Files/Folders to '%s'") % self.widgets.get_widget('entry_new_set_name').get_text())
        self.widgets.get_widget('druid_summary_name').set_text(self.widgets.get_widget('entry_new_set_name').get_text())
        self.widgets.get_widget('druid_summary_desc').set_text(self.widgets.get_widget('entry_new_set_desc').get_text())

    def on_druid_page_3_next(self, widget, event):
        if len(self.filelist) == 0:
            self.dialogs.showerror(_("You cannot create an empty backup set."))
            return True

    def on_button_ssh_path_clicked(self, widget):
        host = self.widgets.get_widget('entry_ssh_host').get_text()
        user = self.widgets.get_widget('entry_ssh_user').get_text()
        if len(host) == 0 or len(user) == 0:
            return True
        filechooser = FileChooser()
        filechooser.set_return_type(filechooser.RETURN_URI)
        filechooser.set_exitnotify(self.filechosen_new_set_ssh_path)
        filechooser.set_title(_("Select a default remote location to backup to."))
        filechooser.show()
        filechooser.set_current_folder_uri("sftp://%s@%s/" %(user, host))

    def filechosen_new_set_ssh_path(self, uri):
        host = self.widgets.get_widget('entry_ssh_host').get_text().replace(".", "\.")
        user = self.widgets.get_widget('entry_ssh_user').get_text()
        patt = re.compile("sftp:/[/]+%s@%s(.*)" % (user, host))
        match = patt.match(uri)
        if len(match.groups()) > 0:
            self.widgets.get_widget('entry_ssh_path').set_text(match.group(1))

    def on_button_default_dest_clicked(self, widget):
        filechooser = FileChooser()
        filechooser.set_return_type(filechooser.RETURN_FILENAME)
        filechooser.set_exitnotify(self.filechosen_new_set_default_dest)
        filechooser.set_title(_("Select a default destination"))
        filechooser.show()

    def filechosen_new_set_default_dest(self, filename):
        self.widgets.get_widget('entry_new_set_def_dest').set_text(filename)

    def on_druid_page_finish_prepare(self, widget, event):
        event.set_buttons_sensitive(False, False, False, False)

    def on_druid_page_finish_finish(self, event, something):
        buset = self.backupsets.get_named_set(self.widgets.get_widget('druid_summary_name').get_text())
        if buset is None:
            buset = backupsets.BackupSet(self.backupsets.configpath)
        buset.name = self.widgets.get_widget('druid_summary_name').get_text()
        if not buset.path:
            buset.path = buset.name
        buset.desc = self.widgets.get_widget('druid_summary_desc').get_text()
        buset.dest = self.widgets.get_widget('druid_summary_dest').get_text()
        buset.removable = self.widgets.get_widget('chk_removable_device').get_active()
        buset.files_include = []
        buset.files_exclude = []
        for f in self.filelist:
            if f[3]:
                buset.files_include.append(f[2])
            else:
                buset.files_exclude.append(f[2])
        try:
            buset.write()
            if buset not in self.backupsets:
                self.backupsets.add(buset)
            if callable(self.exitnotify):
                self.exitnotify(buset)
            self.druid_cleanup()
        except OSError, e:
            self.widgets.get_widget('druid_page_finish').set_text(
                _("ERROR: Couldn't write new set %(name)s: %(error)s") %
                {'name':self.widgets.get_widget('entry_new_set_name').get_text(), 'error':e})

    def on_button_add_to_set_clicked(self, widget):
        for f in self.widgets.get_widget('filechooserwidget1').get_filenames():
            if os.path.isdir(f):
                self.filelist.append([widget.render_icon(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU, "TreeView"),
                                      widget.render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_MENU, "TreeView"),
                                      f, True])
            else:
                self.filelist.append([widget.render_icon(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU, "TreeView"),
                                      widget.render_icon(gtk.STOCK_FILE, gtk.ICON_SIZE_MENU, "TreeView"),
                                      f, True])
        if len(self.filelist) == 1:
            self.widgets.get_widget('druidfilelist_label').set_text(_("1 item"))
        else:
            self.widgets.get_widget('druidfilelist_label').set_text(_("%d items")%len(self.filelist))
        self.widgets.get_widget('filechooserwidget1').unselect_all()

    def on_button_exc_from_set_clicked(self, widget):
        for f in self.widgets.get_widget('filechooserwidget1').get_filenames():
            if os.path.isdir(f):
                self.filelist.append([widget.render_icon(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU, "TreeView"),
                                      widget.render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_MENU, "TreeView"),
                                      f, False])
            else:
                self.filelist.append([widget.render_icon(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU, "TreeView"),
                                      widget.render_icon(gtk.STOCK_FILE, gtk.ICON_SIZE_MENU, "TreeView"),
                                      f, False])
        if len(self.filelist) == 1:
            self.widgets.get_widget('druidfilelist_label').set_text(_("1 item"))
        else:
            self.widgets.get_widget('druidfilelist_label').set_text(_("%d items")%len(self.filelist))
        self.widgets.get_widget('filechooserwidget1').unselect_all()

    def on_button_remove_from_set_clicked(self, widget):
        selection = self.widgets.get_widget('treeview_druidfilelist').get_selection()
        store, row = selection.get_selected()
        if row is not None:
            store.remove(row)
            if len(self.filelist)==1:
                self.widgets.get_widget('druidfilelist_label').set_text(_("1 item"))
            else:
                self.widgets.get_widget('druidfilelist_label').set_text(_("%d items")%len(self.filelist))

    def find_cd_burners(self):

        """ Populate a combo box with the names of available CD/DVD drives """
        try:
            braseromedia
        except NameError:
            error_string = _("No CD burners available, because you do not have the python module \
braseromedia.")
            self.widgets.get_widget('lbl_cd_burner').set_text(error_string)
        else:
            self.drive_sel = braseromedia.DriveSelection()
            self.widgets.get_widget('hbox30').add(self.drive_sel)
            self.drive_sel.show()

    def on_hiddenfiles_toggled(self, event):
        fc = self.widgets.get_widget('filechooserwidget1')
        fc.set_show_hidden(event.get_active())
