#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.
#
# THIS EXAMPLE HAS BEEN UPDATED TO WORK WITH THE BETA VERSION 12 OF PYTHON-TELEGRAM-BOT.
# If you're still using version 11.1.0, please see the examples at
# https://github.com/python-telegram-bot/python-telegram-bot/tree/v11.1.0/examples

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

import sys
sys.path.insert(0, "../demo/")
import engine

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

class PregChatBot:
    def __init__(self):
        # Enable logging
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

        self.logger = logging.getLogger(__name__)

        # Initialize engine
        self.engine = engine.Engine()

        self.QUESTION, self.SUPPORTCONFIRM, self.SUPPORTSUBMIT, self.SUPPORT = range(4)

        # Create the Updater and pass it your bot's token.
        # Make sure to set use_context=True to use the new context based callbacks
        # Post version 12 this will no longer be necessary

        # Get the token here
        with open("../api.token", 'r') as f:
            botToken = f.readlines()[0].strip()

        self.updater = Updater(botToken, use_context=True)

        # Get the dispatcher to register handlers
        self.dp = self.updater.dispatcher

        # Add conversation handler with states
        self.conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],

            states={
                self.QUESTION:          [MessageHandler(Filters.text, self.question)],
                self.SUPPORTCONFIRM:    [MessageHandler(Filters.regex('^(Yes|No)$'), self.supportConfirm), CommandHandler('skip', self.skip_support)],
                self.SUPPORTSUBMIT:     [MessageHandler(Filters.text, self.supportSubmit)]
            },

            fallbacks=[CommandHandler('support', self.support), CommandHandler('cancel', self.cancel)]
        )

        self.dp.add_handler(self.conv_handler)

        # log all errors
        self.dp.add_error_handler(self.error)

        # Start the Bot
        self.updater.start_polling()
        print("Ready")

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()
        print("Ended")


    def start(self, update, context):
        user = update.message.from_user
        update.message.reply_text(
            'Hi {}! My name is PregChatBot. I will answer any question you have with regards to pregnancies. \n'
            'At any point, send /support if you feel like your question(s) are not being satisfyingly answered. \n'
            'Do note that this bot currently does not keep track of the conversation to build up context. \n'
            'Send /cancel to stop talking to me. Send /start if the bot stops responding. \n\n'
            'What\'s bothering your today?'.format(user.first_name))

        return self.QUESTION

    def question(self, update, context):
        user = update.message.from_user
        self.logger.info("User %s asked \'%s\'", user.first_name, update.message.text)

        _r = self.engine.ask(update.message.text)
        
        response = ["\n".join(_r), "\n\n__Send /support any time to send a question to a human.__"]

        update.message.reply_text("".join(response))

        return self.QUESTION

    def support(self, update, context):
        reply_keyboard = [['Yes', 'No']]

        user = update.message.from_user
        self.logger.info("User %s requested for support.", user.first_name)
        update.message.reply_text('Aw snap, would you like to send the question to our question bank?'
            'It will be answered in bulk at a later point in time. ',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

        return self.SUPPORTCONFIRM

    def supportConfirm(self, update, context):
        # Get user to type their question clearly and then use engine.add_to_questionbank

        user = update.message.from_user
        self.logger.info("Request for support %s: %s", user.first_name, update.message.text)

        if update.message.text == "Yes":
            update.message.reply_text('Righty, please type your question clearly and concisely in **1 message**. It will then be sent to my humans to be answered. '
            'You can send /skip if you would like to skip out.')

            return self.SUPPORTSUBMIT
        else:
            update.message.reply_text('Okay, no problem, you can now continue chatting with me. Ask away!')

            return self.QUESTION

    def skip_support(self, update, context):
        user = update.message.from_user
        self.logger.info("Request for support %s: Skipped", user.first_name)

        update.message.reply_text('Okay, no problem, you can now continue chatting with me. Ask away!')

        return self.QUESTION

    def supportSubmit(self, update, context):
        user = update.message.from_user
        self.logger.info("Request for support submission %s: %s", user.first_name, update.message.text)

        self.engine.add_to_questionbank(update.message.text)

        update.message.reply_text('Your question has been sent! You may now continue asking me questions!')

        return self.QUESTION

    def cancel(self, update, context):
        user = update.message.from_user
        self.logger.info("User %s canceled the conversation.", user.first_name)
        update.message.reply_text('Bye! I hope we can talk again some day.',
                                  reply_markup=ReplyKeyboardRemove())

        return ConversationHandler.END

    def error(self, update, context):
        """Log Errors caused by Updates."""
        self.logger.warning('Update "%s" caused error "%s"', update, context.error)


if __name__ == '__main__':
    x = PregChatBot()
