"""Step 06: ask Telegram which bot this token controls. Usage: python3 step06_getme.py your_bot_username"""
import sys

from tg import TelegramError, api

if len(sys.argv) != 2:
    sys.exit("Usage: python3 step06_getme.py your_bot_username")
username = sys.argv[1].lstrip("@")
try:
    bot = api("getMe")
except TelegramError as error:
    sys.exit(str(error))
if bot["username"].lower() != username.lower():
    sys.exit("This token and username belong to different bots.")
print("Verified @" + bot["username"])
