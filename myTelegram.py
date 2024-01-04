# import telebot
# import os
# import subprocess   
# BOT_TOKEN = "5675859548:AAGdW8n3iYqGFsyCgrYw7aUQk6G8F2mIgN8"

# bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# @bot.message_handler(commands=['cut'])
# def cut_prgm(message):
#     os.system('pkill -f new_main.py')
#     bot.reply_to(message, "Cutcut")

# bot.infinity_polling()




# def start(update, context):
#     # Code to start your program in a screen session
#     subprocess.run(["screen", "-S", "122482.TEST", "-X", "stuff", "python3 gain.py"])

# def stop(update, context):
#     # Code to stop your program
#     subprocess.run(["screen", "-S", "122482.TEST", "-X", "stuff", "^C"])

# def balances(update, context):
#     # Get balances using your function
#     balance = getBalancesTelegram()  # Replace with your function
#     update.message.reply_text(f"thorchain: {balance['thorchain']}")
#     update.message.reply_text(f"bybit: {balance['bybit']}")
#     update.message.reply_text(f"maya: {balance['maya']}")
#     update.message.reply_text(f"total: {balance['total']}")

# def gains(update, context):
#     # Get gains using your function
#     gain = read_gains_from_csv(csv_file="csv/dataOpp.csv" )  # Replace with your function
#     update.message.reply_text(f"All time gain: {round(gain['gain_all_time'], 2)}$")
#     update.message.reply_text(f"Last 24 hours gain: {round(gain['last_24h'], 2)}$")
#     update.message.reply_text(f"Last 18 hours gain: {round(gain['last_18h'], 2)}$")
#     update.message.reply_text(f"Last 12 hours gain: {round(gain['last_12h'], 2)}$")
#     update.message.reply_text(f"Last 6 hours gain: {round(gain['last_6h'], 2)}$")
#     update.message.reply_text(f"Last 3 hours gain: {round(gain['last_3h'], 2)}$")
#     update.message.reply_text(f"Last 1 hour gain: {round(gain['last_1h'], 2)}$")


# def main():
#     # Replace 'YOUR_TOKEN' with your bot's token
# # Replace 'YOUR_TOKEN' with your bot's token
#     updater = Updater('6358377947:AAEXvOHAZcmyQrLOINPpuvZnzrtyOR6G-hc')

#     # Get the dispatcher to register handlers
#     dispatcher = updater.dispatcher

#     dispatcher.add_handler(CommandHandler('start', start))
#     dispatcher.add_handler(CommandHandler('stop', stop))
#     dispatcher.add_handler(CommandHandler('balances', balances))
#     dispatcher.add_handler(CommandHandler('gains', gains))

#     # Start the Bot
#     updater.start_polling()
#     updater.idle()

# if __name__ == '__main__':
#     main()

import asyncio
import subprocess
from telegram.ext import Application, CommandHandler
from telegram import Update
# Ensure that getBalancesTelegram and read_gains_from_csv are properly imported
from gain import read_gains_from_csv
from updateBalances import getBalancesTelegram

async def start(update, context):
    # Send a welcome message or instructions
    await update.message.reply_text("Welcome to the bot! Use the commands to interact.")


async def runscript(update, context):
    # Code to start your external program
    subprocess.run(["screen", "-S", "1117413.main", "-X", "stuff", "python3 main.py\n"])
    await update.message.reply_text("Script started.")

async def stopscript(update, context):
    # Code to stop your external program
    subprocess.run(["screen", "-S", "1117413.main", "-X", "stuff", "^C"])
    await update.message.reply_text("Script stopped.")

async def balances(update, context):
    # Get balances using your function
    balance = getBalancesTelegram()  # Replace with your function
    await update.message.reply_text(f"thorchain: {balance['thorchain']}")
    await update.message.reply_text(f"bybit: {balance['bybit']}")
    await update.message.reply_text(f"maya: {balance['maya']}")
    await update.message.reply_text(f"total: {balance['total']}")

async def gains(update, context):
    # Get gains using your function
    gain = read_gains_from_csv(csv_file="csv/dataOpp.csv" )  # Replace with your function
    await update.message.reply_text(f"All time gain: {round(gain['gain_all_time'], 2)}$")
    await update.message.reply_text(f"Last 24 hours gain: {round(gain['last_24h'], 2)}$")
    await update.message.reply_text(f"Last 18 hours gain: {round(gain['last_18h'], 2)}$")
    await update.message.reply_text(f"Last 12 hours gain: {round(gain['last_12h'], 2)}$")
    await update.message.reply_text(f"Last 6 hours gain: {round(gain['last_6h'], 2)}$")
    await update.message.reply_text(f"Last 3 hours gain: {round(gain['last_3h'], 2)}$")
    await update.message.reply_text(f"Last 1 hour gain: {round(gain['last_1h'], 2)}$")

def main():
    # Create an instance of the Application class
    application = Application.builder().token("6358377947:AAEXvOHAZcmyQrLOINPpuvZnzrtyOR6G-hc").build()

    # Add command handlers to the application
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("runscript", runscript))
    application.add_handler(CommandHandler("stopscript", stopscript))
    application.add_handler(CommandHandler("balances", balances))
    application.add_handler(CommandHandler("gains", gains))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
