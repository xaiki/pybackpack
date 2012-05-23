#!/bin/bash

# This script msgstrs which are still valid with a new pybackpack.pot so that
# the .po files do not require translating all over again.

for po in *.po; do
	echo -n "Merging new translations into ${po}"
	if msgmerge -N ${po} pybackpack.pot > new.po; then
		mv new.po ${po}
	fi
done
