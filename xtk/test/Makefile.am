# this is example-file: src/bin/Makefile.am

# additional include paths necessary to compile the C programs
AM_CFLAGS = -I$(top_srcdir)/src -I$(top_srcdir)/ @AM_CFLAGS@ @GTK_CFLAGS@
AM_LDFLAGS = $(top_builddir)/xtk/libxtk-1.0.la @AM_LDFLAGS@ @GTK_LIBS@

test_CPPFLAGS = $(GTK_CFLAGS)
test_LIBS = $(GTK_LIBS) $(top_builddir)/xtk/libxtk-1.0.la
test_LDADD = $(top_builddir)/xtk/libxtk-1.0.la

# the program to build (the names of the final binaries)
bin_PROGRAMS = test

# list of sources for the 'test' binary
test_SOURCES =  test.c
