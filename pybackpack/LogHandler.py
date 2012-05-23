import gtk
import sys
import os

class LogHandler:
	def __init__(self, widget=None, widgets=None, filecount=0, quiet=False):
		self.text = ""
		self.haswidget = False
		self.haswidgets = False
		self.filecount = float(filecount)
		self.currentfile = 0
		self.quiet = quiet

		if widget is not None:
			self.haswidget = True
			self.widget = widget
			self.output_buffer = widget.get_buffer()
		if widgets is not None:
			self.haswidgets = True
			self.widgets = widgets

	def write(self, text):
		if self.haswidgets and self.filecount > 0:
			if text[:23] == "Processing changed file":
				self.currentfile += 1
				p = self.currentfile / self.filecount
				self.widgets.get_widget('progressbar1').set_fraction(p)
			while gtk.events_pending():
				gtk.main_iteration()
		self.text += text
		if self.haswidget and not self.quiet:
			self.output_buffer.insert(self.output_buffer.get_end_iter(), text)
			while gtk.events_pending():
				gtk.main_iteration()

	def get_contents(self):
		return self.text

	def __str__(self):
		return self.text

	def __len__(self):
		return len(self.text)
