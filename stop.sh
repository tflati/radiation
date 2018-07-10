PORT="7590"
ps x | grep "runserver" | grep $PORT | sed 's/^ //g' | cut -d' ' -f 1 | xargs kill
