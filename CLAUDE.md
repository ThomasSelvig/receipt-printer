# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a thermal receipt printer control project with two main components:
- A Discord bot (`discord-bot/bot.py`) that accepts print commands via slash commands
- A test script (`test.py`) for printing random jokes directly to the printer

## Hardware Configuration

The project controls a specific USB thermal printer with these identifiers:
- Vendor ID: 0x1504
- Product ID: 0x0101
- USB endpoints: out_ep=0x02, in_ep=0x81

Use `lsusb -vvv -d 1504:0101 | grep bEndpointAddress` to verify endpoint addresses if needed.

## Dependencies

Required Python packages:
- `discord.py` - Discord bot framework
- `python-escpos` - ESC/POS thermal printer library
- `python-dotenv` - Environment variable loading

## Development Commands

Since this is a Python project without formal package management files, install dependencies manually:
```bash
pip install discord.py python-escpos python-dotenv
```

Run the Discord bot:
```bash
cd discord-bot
python bot.py
```

Test printer functionality:
```bash
python test.py
```

## Environment Setup

The Discord bot requires a `.env` file in the `discord-bot/` directory with:
- `TOKEN` - Discord bot token

## Architecture Notes

Both scripts use the same printer initialization pattern with CP1252 character encoding for Norwegian characters (Æ, Ø, Å). The Discord bot is configured for a specific guild ID (1404898665302331513) and provides a single slash command `/print` that accepts text messages.

The printer setup is consistent across files but `test.py` explicitly sets the character encoding while `bot.py` relies on defaults.