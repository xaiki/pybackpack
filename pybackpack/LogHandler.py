from gi.repository import Gtk
import sys
import os

class LogHandler:
	def __init__(self, widget=None, builder=None, filecount=0, quiet=False):
		self.text = ""
		self.haswidget = False
		self.hasbuilder = False
		self.filecount = float(filecount)
		self.currentfile = 0
		self.quiet = quiet

		if widget is not None:
			self.haswidget = True
			self.widget = widget
			self.output_buffer = widget.get_buffer()
		if builder is not None:
			self.hasbuilder = True
			self.builder = builder

	def write(self, text):
		if self.hasbuilder and self.filecount > 0:
			if text[:23] == "Processing changed file":
				self.currentfile += 1
				p = self.currentfile / self.filecount
				self.builder.get_object('progressbar1').set_fraction(p)
			while Gtk.events_pending():
				Gtk.main_iteration()
		self.text += text
		if self.haswidget and not self.quiet:
			self.output_buffer.insert(self.output_buffer.get_end_iter(), text)
			while Gtk.events_pending():
				Gtk.main_iteration()

	def get_contents(self):
		return self.text

	def __str__(self):
		return self.text

	def __len__(self):
		return len(self.text)
