#! /bin/bash

ext_list="builder diagonal fortran"
for i in $ext_list; do
	cp build/lib.linux-*/tbplas/$i/*.so tbplas/$i
done
