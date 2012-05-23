import os
import sys
import gtk
import gtk.glade
import gobject
import gettext

gtdomain = "pybackpack"
try:
	localedir = os.environ['PBP_LOCALE_DIR']
except:
	localedir = "/usr/share/locale"
gettext.install(gtdomain, localedir, unicode=True)
gtk.glade.bindtextdomain(gtdomain, localedir)
gtk.glade.textdomain(gtdomain)

import version
import backupsets
import rdiff_interface
from gui import Gui

class BackupTool:
    def __init__(self):
        self.homedir = os.environ['HOME']
        self.configpath = os.path.join(self.homedir, '.'+version.APPPATH)

        # Find the user's backup sets
        self.backupsets = backupsets.BackupSets(self.configpath)

        # connect signals to handler functions
        self.gui = Gui(self.backupsets)

        # create a backup set called 'home' that
        # contains the user's entire home directory
        homeexists = False
        for s in self.backupsets:
            if s.name == _('home'):
                homeexists = True
                break
        if not homeexists:
            buset = backupsets.BackupSet(self.backupsets.configpath)
            buset.name = _('home')
            buset.desc = _("A complete backup of your home directory.")
            buset.files_include = [self.homedir]
            buset.dest = 'cdrw://'
            buset.path = 'home'
            buset.write()
            self.backupsets.add(buset)

        # populate the list of recently used backup/restore locations
        try:
            for line in open(os.path.join(self.configpath, "backup_mru")).readlines():
                self.gui.add_prev_dest(line.strip())
            for line in open(os.path.join(self.configpath, "restore_src")).readlines():
                self.gui.add_prev_restore_loc(line.strip())
        except IOError:
            pass #if the file doesn't exist, don't panic!

        gtk.main()

def StartUp():
    BackupTool()


if __name__ == '__main__':
	StartUp()
