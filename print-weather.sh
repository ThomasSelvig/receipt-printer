weather="$(curl 'https://wttr.in/Tøyen?0dnqFT&lang=nb')"
curl 192.168.50.19:8000/print/text -d "text=${weather}"
