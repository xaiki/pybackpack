from gi.repository import Gtk

import os

class FileChooser:

    """FileChooser provides a general interface to a file chooser
       which encapsulates the settings that are most often used in
       the program. It returns the selected file using a callback
       interface which is passed the selected filename or uri, depending
       on which return type was asked for using set_return_type()."""

    def __init__(self):

        """Set up a new FileChooser object. The GUI data for the file
           chooser dialog are read from a glade file."""

        self.RETURN_URI = 0
        self.RETURN_FILENAME = 1

        path = os.path.dirname(__file__)
        if path:
            path += "/"

        self.exitnotify = None
        try:
            self.builder = Gtk.Builder()
            self.builder.add_from_file(path + "filechooser.ui")
        except RuntimeError:
            dlg = Gtk.MessageDialog(None,  Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
                                    Gtk.ButtonsType.CLOSE,
                                    _("Unable to initialise filechooser"))
            dlg.connect("response", lambda w: Gtk.main_quit())

        self.builder.connect_signals(self)
        self.dialog = self.builder.get_object("filechooserdialog1")
        self.dialog.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.title = ""

    def set_return_type(self, type):

        """Tell the FileChooser what format you'd like the selected
           file name to be returned in. Choose from the RETURN_* values
           in the FileChooser class."""

        self.return_type = type

    def set_title(self, title=""):

        """Set the title of the file chooser dialog box."""

        self.title = title
        self.dialog.set_title(title)

    def set_current_folder_uri(self, uri):

        """Set the folder path that the file chooser dialog should show."""

        self.dialog.set_current_folder_uri(uri)

    def set_exitnotify(self, exitnotify):

        """Set the callback that is called once a folder has been selected.
           the callback function should accept one string argument which
           will be a filename in the format specified in set_return_type()."""

        self.exitnotify = exitnotify

    def show(self):

        """Display the file chooser dialog and allow the user to select
           files from it."""

        self.dialog.show()

    def on_filechooserdialog1_show(self, widget):

        """Called when the file chooser dialog is displayed.
           Sets the current folder to the user's home directory."""

        widget.set_current_folder(os.environ['HOME'])

    def on_filechooser_open_clicked(self, event):

        """Called when the user selects a file and clicks on the open button.
           Calls the exitnotify callback specified in set_exitnotify() and
           then hides the file chooser dialog."""

        if callable(self.exitnotify):
            if self.return_type == self.RETURN_URI:
                self.exitnotify(self.dialog.get_uri())
            elif self.return_type == self.RETURN_FILENAME:
                self.exitnotify(self.dialog.get_filename())
        self.dialog.hide()

    def on_filechooser_cancel_clicked(self, event):

        """Called when the user cancels the file chooser dialog.
           Hides the file chooser dialog."""

        self.dialog.hide()

if __name__ == "__main__":
    def _(m):
        return m

    from gi.repository import GLib

    f = FileChooser()
    f.show()

    GLib.timeout_add_seconds(2, lambda x: Gtk.main_quit(), None)
    Gtk.main()
