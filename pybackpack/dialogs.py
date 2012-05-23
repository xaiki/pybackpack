from gi.repository import Gtk

class Dialogs:

    '''A utility class providing simple access to common dialog boxes
       and the user input from them.'''

    def __init__(self, parent):

        '''Initialise member variables to sane defaults.'''

        self.response = None
        self.parent = parent

    def showerror(self, message):

        '''Show an error dialog box with a message and store the user's response.'''

        dlg = Gtk.MessageDialog(self.parent, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
                                                    Gtk.ButtonsType.OK, message)
        dlg.connect("response", self._dlgresponse)
        dlg.show()

    def showmsg(self, message):

        '''Show a message dialog box with a message and store the user's response.'''

	dlg = Gtk.MessageDialog(self.parent, Gtk.DialogFlags.MODAL, Gtk.MessageType.INFO,
                                                   Gtk.ButtonsType.OK, message)
        dlg.connect("response", self._dlgresponse)
        dlg.show()

    def showinfo(self, message):

        '''Show an information dialog box with a message and store the user's response.'''

        self.response = None
        dlg = Gtk.MessageDialog(self.parent, Gtk.DialogFlags.MODAL, Gtk.MessageType.INFO,
                                           Gtk.ButtonsType.OK_CANCEL, message)
        dlg.connect("response", self._dlgresponse)
        dlg.show()

    def showyesno(self, message):

        '''Show a Yes/No dialog box with a message and store the user's response.'''

        self.response = None
        dlg = Gtk.MessageDialog(self.parent, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
                           Gtk.ButtonsType.YES_NO, message)
        dlg.connect("response", self._dlgresponse)
        dlg.show()

    def _dlgresponse(self, widget, response):
        widget.destroy()
        self.response = response

if __name__ == "__main__":
    from gi.repository import GLib
    w = Gtk.Window()
    w.connect("destroy", lambda x,y: Gtk.main_quit())
    d = Dialogs(w)
    d.showerror("error")
    d.showmsg("msg")
    d.showinfo("info")
    d.showyesno("yesno")

    GLib.timeout_add_seconds(2, lambda x: Gtk.main_quit(), None)
    Gtk.main()
