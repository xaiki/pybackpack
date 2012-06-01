# initial information about the project
AC_INIT([Xtk],[3.0],[xaiki@evilgiggle.com])

# check if the source folder is available
AC_CONFIG_SRCDIR([xtk/gtkcellrendererwidget.c])

# Checks for programs.
AC_PROG_CC
AC_PROG_CC_C_O
AC_PROG_CC_STDC
AC_PROG_INSTALL
AC_PROG_MAKE_SET
AC_PROG_LIBTOOL

# automake initialization (mandatory) including a check for automake API version >= 1.11
AM_INIT_AUTOMAKE([1.11 -Wall no-define -Wno-portability tar-ustar no-dist-gzip dist-xz])
AM_MAINTAINER_MODE([enable])
AC_CONFIG_MACRO_DIR([m4])

# use the C++ compiler for the following checks
AC_LANG([C])

# Version
XTK_MAJOR_VERSION=1
XTK_MINOR_VERSION=0
XTK_MICRO_VERSION=0
XTK_VERSION=$XTK_MAJOR_VERSION.$XTK_MINOR_VERSION.$XTK_MICRO_VERSION

XTK_LT_CURRENT=1
XTK_LT_REVISION=0
XTK_LT_AGE=0

AC_SUBST(XTK_VERSION)
AC_SUBST(XTK_LT_CURRENT)
AC_SUBST(XTK_LT_REVISION)
AC_SUBST(XTK_LT_AGE)

# required versions of other packages
m4_define([gtk_required_version], [3.0])
m4_define([introspection_required_version], [1.32.0])

GTK_REQUIRED_VERSION=gtk_required_version
INTROSPECTION_REQUIRED_VERSION=introspection_required_version

AC_SUBST(GTK_REQUIRED_VERSION)
AC_SUBST(INTROSPECTION_REQUIRED_VERSION)

PKG_CHECK_MODULES(GTK,
  [gtk+-3.0 >= gtk_required_version])

##################################################
# GObject introspection
##################################################

GOBJECT_INTROSPECTION_CHECK(introspection_required_version)

GTK_PREFIX="`$PKG_CONFIG --variable=prefix gtk+-3.0`"

AC_SUBST(GTK_PREFIX)

# Checks for typedefs, structures, and compiler characteristics.
AC_TYPE_SIZE_T

dnl Initialize libtool
LT_PREREQ([2.2.6])
LT_INIT([disable-static win32-dll])
# Create libtool early, because it's used in configure
LT_OUTPUT

# distribute additional compiler and linker flags among Makefiles
# --> set and change these variables instead of CXXFLAGS or LDFLAGS (for user only)
AC_SUBST([AM_CFLAGS])
AC_SUBST([AM_LDFLAGS])

# files to generate via autotools (prepare .am or .in source files)
AC_CONFIG_FILES([Makefile])
AC_CONFIG_FILES([xtk/Makefile
		 test/Makefile
		 xtk.pc])

# finally this generates the Makefiles etc. for the build
AC_OUTPUT
