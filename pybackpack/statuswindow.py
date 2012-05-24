from gi.repository import Gtk

import os
import time

class StatusWindow:

    """StatusWindow provides a graphical window into which messages are
       added. The messages are timestamped and put on a new line."""

    def __init__(self):

        """Set up a new status window."""
        try:
            self.builder = Gtk.Builder()
            self.builder.add_from_file("%s/statuswindow.ui"
                                       %(os.path.realpath(os.path.dirname(__file__))))
        except RuntimeError:
            dlg = Gtk.MessageDialog(None,  Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
                                    Gtk.ButtonsType.CLOSE,
                                    _("Failed to initialise status window."))
            dlg.connect("response", lambda w: Gtk.main_quit())

        # Connect signals to handler functions
        self.builder.connect_signals(self)

    def show(self):

        """Make the status window visible."""

        self.builder.get_object('window_output_log').show()

    def addmsg(self, msg):

        """Adds a timestamped message to the status window."""

        buf = self.builder.get_object('output_log').get_buffer()
        buf.insert(buf.get_end_iter(), "%s: %s\n" % (time.ctime(), msg))

    def get_buffer(self):

        """Returns the text buffer of the status window."""

        return self.builder.get_object('output_log').get_buffer()

    def scroll(self):

        """Scrolls the status text box to the end."""

        self.builder.get_object('output_log').scroll_to_iter(
            self.builder.get_object('output_log').get_buffer().get_end_iter(), 0)

    def on_button_output_log_close_clicked(self, widget):

        """Hides the status window when the close button is clicked."""

        self.builder.get_object('window_output_log').hide()

    def on_window_output_log_delete_event(self, widget, event):

        """Hide the status window when the x is clicked."""

        widget.hide()
        return True

if __name__ == "__main__":
    from gi.repository import GLib
    s = StatusWindow()

    s.show()

    GLib.timeout_add_seconds(10, lambda x: Gtk.main_quit(), None)
    Gtk.main()
