#!/bin/bash

POFILE="$1"
if [ ! -r "$POFILE" ]; then
	echo "Error: .po file \"${POFILE}\" could not be read."
	exit 1;
fi

LNG=$(echo "$POFILE" | sed 's/\.po$//')
MODIR="/tmp/pybackpack-test/mo/${LNG}/LC_MESSAGES"

mkdir -p "$MODIR"
msgfmt -v "$POFILE" -o "$MODIR"/pybackpack.mo

PBP_LOCALE_DIR="/tmp/pybackpack-test/mo" python ../pybackpack/backuptool.py
