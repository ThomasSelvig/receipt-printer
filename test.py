from random import choice

from escpos.printer import Usb

# vendor id, product id, lsusb -vvv -d 1504:0101 | grep bEndpointAddress
p = Usb(0x1504, 0x0101, out_ep=0x02, in_ep=0x81)
p.charcode("CP1252")

def get_joke():
    jokes = [
        "Why did the thermal receipt printer break up with its partner?\nIt just couldn’t handle the heat of the moment!",
        "What did the thermal receipt printer say to the paper?\n“You complete me, but I’m still going to roll with it!”",
        "Why did the thermal receipt printer get invited to all the parties?\nBecause it always knew how to print a good time!",
        "How does a thermal receipt printer stay in shape?\nIt does a lot of “roll” exercises!",
        "Why did the thermal receipt printer apply for a job?\nIt wanted to make some “cents” in the world!",
        "What did one thermal receipt printer say to the other at the coffee shop?\n“I can’t espresso how much I love a good brew!”",
        "Why was the thermal receipt printer always calm?\nBecause it knew how to keep its cool under pressure!",
        "What do you call a thermal receipt printer that tells jokes?\nA pun-derful machine!",
        "Why did the thermal receipt printer get a promotion?\nIt always delivered results on time, no matter how heated the situation!",
        "How do thermal receipt printers flirt?\nThey say, “You’ve got my heart racing, and I’m ready to roll with you!”",
    ]

    return choice(jokes)


p.text(f"{get_joke()}")
# p.text("Her er en Ææ, en Øø, og en Åå. ^*̈́''¨`+\\`=)(/&%¤#\"!.,-)")
p.cut()
