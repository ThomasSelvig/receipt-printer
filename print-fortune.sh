fortune="$(/usr/games/fortune | /usr/games/cowsay)"
curl 192.168.50.19:8000/print/text -d "text=${fortune}"
