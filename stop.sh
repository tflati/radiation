PORT="7565"
ps x | grep "runserver" | grep $PORT | sed 's/^ //g' | cut -d' ' -f 1 | xargs kill
