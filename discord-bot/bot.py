from io import BytesIO
from os import getenv

from PIL import Image
import discord
from discord.ext import commands
from dotenv import load_dotenv
from escpos.printer import Usb
import requests

load_dotenv()

bot = commands.Bot()
guilds = [1404898665302331513, 455152675617767424]

# vendor id, product id, lsusb -vvv -d 1504:0101 | grep bEndpointAddress
p = Usb(0x1504, 0x0101, out_ep=0x02, in_ep=0x81)


@bot.slash_command(name="print-tekst", guild_ids=guilds)
async def print_tekst(ctx, melding: str):
    p.text(melding)
    p.cut()
    await ctx.respond("Printet meldingen.")

@bot.slash_command(name="print-bilde", guild_ids=guilds)
async def print_bilde(ctx, bilde: discord.Attachment):

    if bilde.content_type and "image" in bilde.content_type:
        # save image to in-memory file object
        response = requests.get(bilde.url)
        if response.status_code == 200:
                try:
                    image = Image.open(BytesIO(response.content))
                    
                    # Resize image if width exceeds 512px
                    max_width = 512
                    if image.width > max_width:
                        aspect_ratio = image.height / image.width
                        new_height = int(max_width * aspect_ratio)
                        image = image.resize((max_width, new_height))
                    
                    p.image(image)
                    p.cut()
                    await ctx.respond("Printet bildet.")
                    return
                except IOError:
                    print("Cannot open image from response content.")
                    await ctx.respond("Kunne ikke printe bildet: Feil ved åpning av bilde.")
                    return
        else:
            await ctx.respond("Kunne ikke printe bildet: Feil ved nedlastning av bilde.")
            return
    else:
        await ctx.respond("Kunne ikke printe bildet: Fil ikke gjenkjent som et bilde.")
        return


bot.run(getenv("TOKEN", ""))
