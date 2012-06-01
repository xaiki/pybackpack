from gi.repository import Gtk

import os
import rdiff_interface
from sys import stderr
from ConfigParser import SafeConfigParser, NoOptionError

class BackupSet:

    """Holds data about a set of files to backup."""

    def __init__(self, configpath):

        """Initialise a BackupSet"""

        self.setspath = os.path.join(configpath,"sets")
        self._includes = {}
        self._excludes = {}
        self.name = ""
        self.path = ""
        self.desc = ""
        self._dest = ""
        self.rdiff = None
        self.avail = "UNIMPLEMENTED"
        self.removable = False
        self.filelist = Gtk.ListStore(str , str , str , bool)

    def delete(self):

        """Removes the data files for this backup set."""
        if self.name is not _('home'):
            try:
                os.remove(os.path.join(self.setspath, self.name, "set.ini"))
                os.remove(os.path.join(self.setspath, self.name, "filelist"))
                os.rmdir(os.path.join(self.setspath, self.name))
            except OSError, e:
                print >> stderr, e

    def write(self):

        """Writes set.ini and filelist for this backup set to a
           new or existing set directory."""

        try:
            os.makedirs(os.path.join(self.setspath, self.name))
        except OSError, e:
            if str(e)[7:9]=="17":
                pass
            else:
                raise OSError(e)

        cp = SafeConfigParser()
        cp.add_section("Set")
        cp.set("Set", "name", str(self.name))
        cp.set("Set", "desc", str(self.desc))
        cp.set("Set", "dest", str(self._dest))
        cp.set("Set", "removable", str(self.removable))
        # TODO: Find out which other keys we use (if any)

        inifile = open(os.path.join(self.setspath, self.name, "set.ini"), "w")
        cp.write(inifile)
        inifile.close()

        flist = open(os.path.join(self.setspath, self.name, "filelist"), "w")

        for path in self.get_excludes():
            flist.write("- %s\n" % path)

        for path in self.get_includes():
            flist.write("+ %s\n" % path)

        flist.write("- **\n")
        flist.close()

    def set_dest (self, s):
        self.rset = rdiff_interface.ParseRestoreSrc(s)
        self._dest = s

    def get_dest (self):
        return self._dest

    def get_model (self):
        return self.filelist

    def get_includes (self):
        return self._includes.keys()

    def get_excludes (self):
        return self._excludes.keys()

    def remove (self, f):
        for p in self.filelist:
            if p[2] == f:
                i = self.filelist.iter_nth_child
                self.filelist.remove(p.iter)
                if self._excludes.has_key(f):
                    del self._excludes[f]
                elif self._includes.has_key(f):
                    del self._includes[f]
                return True
        return False

    def _check_add (self, f, inc):
        if inc == True:
            if f in self._includes:
                return True
            if f in self._excludes:
                self.remove (f)
            self._includes[f] = True
        else:
            if f in self._excludes:
                return True
            if f in self._includes:
                self.remove (f)
            self._excludes[f] = True
        return True

    def add_exclude (self, f):
        return self.add(f, inc=False)

    def add_include (self, f):
        return self.add(f, inc=True)

    def get_stock(self):
        if self.get_dest()[:7] == "sftp://":
            return Gtk.STOCK_NETWORK
        elif self.get_dest()[:7] == "cdrw://":
            return Gtk.STOCK_CDROM
        return Gtk.STOCK_DIRECTORY

    def get_icon_name(self):
        if self.get_dest()[:7] == "sftp://":
            return "gnome-fs-ssh"
        elif self.get_dest()[:7] == "cdrw://":
            return "gnome-dev-disc-cdrw"
        return "gnome-dev-harddisk"


    def add (self, f, inc=True):
        if f == "**":
            print "Skipping malformated file: **", inc
            return
        widget = Gtk.Image()
        icon = []

        if os.path.isdir(f):
            icon.append(Gtk.STOCK_DIRECTORY)
        else:
            icon.append(Gtk.STOCK_FILE)

        if inc == True:
            icon.append(Gtk.STOCK_ADD)
        else:
            icon.append(Gtk.STOCK_REMOVE)

        self.filelist.append([icon.pop(),
                              icon.pop(),
                              f, True])

    def __str__(self):

        """Returns a string representation of a backup set.
           Useful for debugging."""

        s = "Backup set: " + self.name
        s += "\n`Files to include: " + str(self.get_includes())
        s += "\n Files to exclude: " + str(self.get_excludes())
        s += "\n Path: " + self.path
        s += "\n Desc: " + self.desc
        s += "\n Dest: " + self._dest
        s += "\n `Removable: " + str(self.removable)
	return s

class BackupSets:

    """BackupSets provides an interface to the user defined
       backup sets specified in the specified config path."""

    def __init__(self, configpath):

        """Load the backup set data and initialise members."""

        self.configpath = configpath
        self.setspath = os.path.join(configpath,"sets")
        self.change_hooks = []
        self.backupsets = []
        self._findsets()

    def add(self, buset):

        """Register a backup set in the list."""

        if isinstance(buset, BackupSet) and buset not in self.backupsets:
            self.backupsets.append(buset)
            self._changed()

    def remove(self, buset):

        """Remove a backup set from the list."""

        try:
            self.backupsets.remove(buset)
            self._changed()
        except ValueError:
            pass

    def count(self):

        """Return the number of backup sets."""

        return len(self.backupsets)

    def get_named_set(self, name):

        """Find a backup set by its name. Returns None if not found."""

        for bset in self.backupsets:
            if bset.name == name:
                return bset
        return None

    def add_change_hook(self, hook):

        """Register a callback to be called when the list of backup sets changes."""

        # TODO: check number of arguments accepted is correct, perhaps
        if callable(hook):
            self.change_hooks.append(hook)

    def remove_change_hook(self, hook):

        """Remove a change hook from the list, if it's in there."""

        try:
            self.change_hooks.remove(hook)
            self._changed()
        except ValueError:
            pass # It wasn't in the list, no worries

    def _changed(self):

        """Fire off a signal when the backup sets change."""

        for kerpoke in self.change_hooks:
            if callable(kerpoke):
                kerpoke()

    def _findsets(self):

        """Finds all backup sets in the user's home directory"""

        self.backupsets = []
        if os.path.exists(self.setspath):
            sets = [x for x in os.listdir(self.setspath) if
                       os.path.isdir(os.path.join(self.setspath,x))]
            sets.sort()
            for bset in sets:
                buset = BackupSet(self.configpath)
                buset.path = bset
                if not os.path.exists(os.path.join(self.setspath, bset, "filelist")):
                    print >> stderr, _("No 'filelist' for %s") % bset
                    continue
                filelist = open(os.path.join(self.setspath, bset, "filelist")).readlines()
                for l in filelist:
                    if l[0] == "#":
                        continue
                    elif l[0] == "-":
                        buset.add_exclude(l[2:].strip())
                    elif l[0] == "+":
                        buset.add_include(l[2:].strip())
                    else:
                        continue
                cp = SafeConfigParser()
                inifile = os.path.join(self.setspath, bset, "set.ini")
                if cp.read(inifile) == []:
                    print >> stderr, _("Couldn't read in description file: %s") % inifile
                    continue
                try:
                    buset.name = cp.get('Set', 'name')
                    buset.desc = cp.get('Set', 'desc')
                    buset.set_dest(cp.get('Set', 'dest'))
                    rm = cp.get('Set', 'removable')
                    if rm == 'True':
                        buset.removable = True
                    # TODO: Find out which other keys we need to load

                except NoOptionError, e:
                    print >> stderr, _("Couldn't parse %(filename)s fully: %(error)s") % {'filename':inifile, 'error':e}

                self.backupsets.append(buset)

        if len(self.backupsets) > 0:
            self._changed()

    def __iter__(self):

        """Generator function to iterate over the backup sets."""

        for index in self.backupsets:
            yield index
