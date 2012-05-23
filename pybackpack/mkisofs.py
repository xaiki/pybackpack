from subprocess import Popen
from subprocess import PIPE

class Mkisofs:
    
    """Mkisofs is a wrapper for the genisoimage program. It simplifies 
    calls to genisoimage and tracks its progress. An optional hook is 
    provided which will be called whenever a percentage progress is 
    reported by genisoimage."""

    def __init__(self):
        self.progress_hook = None
        self.progress = 0.0
        self.retval = None

    def set_progress_hook(self, hook=None):
        
        """Sets the progress hook function to the argument hook. The 
        function specified by hook should accept a floating point number 
        as its only argument."""

        if (callable(hook)):
            self.progress_hook = hook

    def _set_progress(self, progress):
        try:
            self.progress = float(progress)
        except ValueError:
            pass

    def report_progress(self):
        
        """Calls the progress hook if one has been specified."""

        if callable(self.progress_hook):
            self.progress_hook(self.progress)

    def create_iso(self, source, isofile):

        """Takes a source file path and creates an iso file with it, which 
        is written to the isofile path. genisoimage is called with option -r. 
        See the genisoimage manual for details"""
        
        args = ["genisoimage","-r","-o",isofile,source]
        mkisofs = Popen(args, 1, stdout=PIPE, stderr=PIPE)
        self.retval = mkisofs.poll()
        while (self.retval is None):
            output = mkisofs.stderr.readline()
            if (output != ""):
                progress = output.split()[0]
                if (progress[-1:] == '%'):
                    self._set_progress(progress[:-1])
                    self.report_progress()
            self.retval = mkisofs.poll()

    def get_retval(self):

        """Gets the value returned by genisoimage or None if it hasn't 
        finished a run."""
        
        return self.retval
