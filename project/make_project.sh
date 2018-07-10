#!/bin/bash

set +x

replace_name=$1
name=$2
from_name="engine"

if [ "$#" -ge 3 ]
then
    from_name=$3
fi

sed -i 's/'${replace_name}'/'${name}'/g' ${from_name}/index.html
sed -i 's/'${replace_name}'/'${name}'/g' ${from_name}/components/element/elementController.js
sed -i 's/'${replace_name}'/'${name}'/g' ${from_name}/components/table/my_custom_element/myCustomElement.js

for file in $(ls material/)
do
	echo "Creating symlink from ${from_name}/$file to material/$file"
	ln -s ../material/$file ${from_name}/$file
done
