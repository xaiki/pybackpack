import os
import time
import gtk
import gtk.glade

class StatusWindow:

    """StatusWindow provides a graphical window into which messages are
       added. The messages are timestamped and put on a new line."""

    def __init__(self):

        """Set up a new status window."""

        try:
            self.widgets = gtk.glade.XML("%s/statuswindow.glade"
                           % os.path.dirname(__file__))
        except RuntimeError:
            gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, 
                  gtk.BUTTONS_CLOSE,_("Failed to initialise status window."))

        self.widgets.signal_autoconnect(self)

    def show(self):

        """Make the status window visible."""

        self.widgets.get_widget('window_output_log').show()

    def addmsg(self, msg):

        """Adds a timestamped message to the status window."""

        buf = self.widgets.get_widget('output_log').get_buffer()
        buf.insert(buf.get_end_iter(), "%s: %s\n" % (time.ctime(), msg))

    def get_buffer(self):

        """Returns the text buffer of the status window."""

        return self.widgets.get_widget('output_log').get_buffer()

    def scroll(self):

        """Scrolls the status text box to the end."""

        self.widgets.get_widget('output_log').scroll_to_iter(
            self.widgets.get_widget('output_log').get_buffer().get_end_iter(), 0)

    def on_button_output_log_close_clicked(self, widget):

        """Hides the status window when the close button is clicked."""

        self.widgets.get_widget('window_output_log').hide()
    
    def on_window_output_log_delete_event(self, widget, event):

        """Hide the status window when the x is clicked."""

        widget.hide()
        return True

