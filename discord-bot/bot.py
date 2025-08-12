from os import getenv

import discord
from discord.ext import commands
from dotenv import load_dotenv
from escpos.printer import Usb

load_dotenv()

bot = commands.Bot()

# vendor id, product id, lsusb -vvv -d 1504:0101 | grep bEndpointAddress
p = Usb(0x1504, 0x0101, out_ep=0x02, in_ep=0x81)


@bot.slash_command(name="print", guild_ids=[1404898665302331513])
async def print(ctx, melding: str):
    p.text(melding)
    p.cut()
    await ctx.respond("Printet meldingen.")


bot.run(getenv("TOKEN", ""))
