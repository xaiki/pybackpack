import gtk

class Dialogs:

    '''A utility class providing simple access to common dialog boxes
       and the user input from them.'''

    def __init__(self, parent):

        '''Initialise member variables to sane defaults.'''

        self.response = None
        self.parent = parent

    def showerror(self, message):

        '''Show an error dialog box with a message and store the user's response.'''

        dlg = gtk.MessageDialog(self.parent, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,
                                                    gtk.BUTTONS_OK, message)
        dlg.connect("response", self._dlgresponse)
        dlg.show()

    def showmsg(self, message):
        
        '''Show a message dialog box with a message and store the user's response.'''

    	dlg = gtk.MessageDialog(self.parent, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO,
                                                    gtk.BUTTONS_OK, message)
        dlg.connect("response", self._dlgresponse)
        dlg.show()

    def showinfo(self, message):

        '''Show an information dialog box with a message and store the user's response.'''

        self.response = None
        dlg = gtk.MessageDialog(self.parent, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO,
                                            gtk.BUTTONS_OK_CANCEL, message)
        dlg.connect("response", self._dlgresponse)
        dlg.show()

    def showyesno(self, message):

        '''Show a Yes/No dialog box with a message and store the user's response.'''

        self.response = None
        dlg = gtk.MessageDialog(self.parent, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
                            gtk.BUTTONS_YES_NO, message)
        dlg.connect("response", self._dlgresponse)
        dlg.show()

    def _dlgresponse(self, widget, response):
        widget.destroy()
        self.response = response
