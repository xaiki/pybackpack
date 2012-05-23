#!/usr/bin/env python
import os
import sys
import glob
import shutil
from pybackpack import version
from distutils.log import info
from distutils.core import setup
from distutils.cmd import Command
from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean
from distutils.command.install_data import install_data as _install_data

version_string = version.VERSION

class build_mo(Command):
	description = "build .mo message catalogues from .po files"
	user_options = [('build-base=', 'b', 'base directory for build library')]
	def initialize_options(self):
		self.build_base = None

	def finalize_options(self):
		if self.build_base is None:
			self.build_base = 'build'

	def __mo_newer(self, po_file, mo_file):
		po_stat = os.stat(po_file)
		mo_stat = os.stat(mo_file)

		if mo_stat.st_mtime >= po_stat.st_mtime:
			return True
		else:
			return False

	def run(self):
		for po_file in glob.glob("po/*.po"):
			locale = os.path.basename(po_file)[:-3]
			mo_dir = os.path.join(self.build_base, "locale", locale, "LC_MESSAGES")
			mo_file = os.path.join(mo_dir, "pybackpack.mo")
			if not os.path.isdir(mo_dir):
				info("creating %s" % mo_dir)
				os.makedirs(mo_dir)
			if not (os.path.isfile(mo_file) and self.__mo_newer(po_file, mo_file)):
				info("compiling '%s'" % mo_file)
				os.system("msgfmt %s -o %s" % (po_file, mo_file))


class build(_build):
	def run(self):
		_build.run(self)
		self.run_command('build_mo')

class install_data(_install_data):
	def finalize_options(self):
		_install_data.finalize_options(self)
		mo_files = os.path.join("build","locale","*","LC_MESSAGES","pybackpack.mo")
		locale_dir = os.path.join('share','locale')
		patt = os.path.join("build", "locale", "*", "LC_MESSAGES", "pybackpack.mo")
		for mo in glob.glob(patt):
			lang = os.path.basename(os.path.dirname(os.path.dirname(mo)))
			dest_dir = os.path.join("share","locale",lang,"LC_MESSAGES")
			self.data_files.append((dest_dir, [mo]))


class clean(_clean):
	def run(self):
		locale_dir = os.path.join(self.build_base, 'locale')
		if self.all and os.path.exists(locale_dir):
			info("removing %s (and everything under it)" % locale_dir)
			try:
				shutil.rmtree(locale_dir)
			except:
				pass
		_clean.run(self)

setup(name="pybackpack",
	version=version_string,
	description="A program to perform backups and restores of user data",
	author="Andrew Price",
	author_email="andy@andrewprice.me.uk",
	url="http://andrewprice.me.uk/projects/pybackpack",
	packages = ['pybackpack'],
	package_dir = {'pybackpack': 'pybackpack'},
	package_data = {'pybackpack': ['*.glade']},
	scripts = ['scripts/pybackpack'],
	data_files = [
		('share/applications', ['data/pybackpack.desktop']),
		('share/man/man1', ['docs/pybackpack.1']),
		('share/pixmaps', ['pybackpack/pybackpack_logo.png'])
		],
	cmdclass = {
		'install_data': install_data,
		'build_mo': build_mo,
		'build': build,
		'clean': clean
		}
	)
