import os

def FindFiles(base=None):
	"""Scans the directory at base (defaults to home directory)
	for known files+settings"""
	db = {
		"Gaim" : ".gaim/",
		"Firefox" : ".mozilla/firefox/",
		"Thunderbird" : ".thunderbird/",
		"Thunderbird" : ".mozilla-thunderbird/"
	}
	found = []

	if base == None:
		base = os.path.expanduser("~")
	if base[:-1] != "/":
		base += "/"

	for name,path in db.items():
		if os.path.exists(base+path):
			print _("Found %s settings.") % name
			found.append((name, base+path))

	return found
