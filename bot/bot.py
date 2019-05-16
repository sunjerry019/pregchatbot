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

import sys, os
_pwd = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_pwd, "../demo/"))

import engine

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

from systemd.daemon import notify, Notification
from systemd import journal
import uuid

class PregChatBot:
    def __init__(self):
        # Enable logging
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

        self.logger = logging.getLogger(__name__)

        # Systemd journal handler
        self.logger.addHandler(journal.JournaldLogHandler())

        # Initialize engine
        self.engine = engine.Engine()

        self.QUESTION, self.SELECTQUESTION, self.SUPPORTCONFIRM, self.SUPPORTSUBMIT, self.SUPPORT = range(5)

        # Create the Updater and pass it your bot's token.
        # Make sure to set use_context=True to use the new context based callbacks
        # Post version 12 this will no longer be necessary

        # Get the token here
        _pwd = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(_pwd, "../api.token"), 'r') as f:
            botToken = f.readlines()[0].strip()

        self.updater = Updater(botToken, use_context=True)

        # Get the dispatcher to register handlers
        self.dp = self.updater.dispatcher

        # Add conversation handler with states
        self.conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],

            states={
                self.QUESTION:          [MessageHandler(Filters.text, self.question)],
                self.SELECTQUESTION:    [MessageHandler(Filters.text, self.selectQuestion)],
                self.SUPPORTCONFIRM:    [MessageHandler(Filters.regex('^(Yes|No)$'), self.supportConfirm), CommandHandler('skip', self.skip_support)],
                self.SUPPORTSUBMIT:     [MessageHandler(Filters.text, self.supportSubmit)]
            },

            fallbacks=[CommandHandler('support', self.support), CommandHandler('cancel', self.cancel), CommandHandler('help', self.help)]
        )

        self.dp.add_handler(self.conv_handler)

        # log all errors
        self.dp.add_error_handler(self.error)

        # Start the Bot
        self.updater.start_polling()
        print("Ready")
        notify(Notification.READY)

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()
        notify(Notification.STOPPING)
        print("Ended")


    def start(self, update, context):
        user = update.message.from_user
        update.message.reply_text(
            'Hi {}! My name is PregChatBot. I will answer any question you have with regards to pregnancies. \n'
            'At any point, send /support if you feel like your question(s) are not being satisfyingly answered. \n'
            'Do note that this bot currently does not keep track of the conversation to build up context. \n'
            'Send /cancel to stop talking to me. Send /start if the bot stops responding. \n\n'
            'What\'s bothering you today?'.format(user.first_name), parse_mode=ParseMode.MARKDOWN)

        return self.QUESTION

    def help(self, update, context):
        user = update.message.from_user
        self.logger.info("User %s asked for help", user.first_name)

        update.message.reply_text("PregChatBot v0.1\n\nThis is a bot that answers your queries on anything relating to pregnancies!\n\n/start - Start a conversation with me\n/support - Send a question to a human\n/cancel - Stop talking to me\n/help - Display this help screen".format(update.message.text))

        # https://stackoverflow.com/a/55759244/3211506
        return None

    def question(self, update, context):
        user = update.message.from_user
        self.logger.info("User %s asked \'%s\'", user.first_name, update.message.text)

        if update.message.text.lower() in { "hi": 1, "hello": 1, "hey": 1 }:
            update.message.reply_text(update.message.text + "! Anything on your mind right now regarding pregnancies?")
            return None

        if update.message.text.lower() == "no":
            update.message.reply_text("It's okay, you can come bother me anytime when you have questions. ")
            return None

        _r = self.engine.ask(update.message.text)

        if len(_r):
            reply_keyboard = [ [x] for x in _r ]

            response = ["I found these similiar questions in my database, please choose the one that best matches your query. ^^\n\n"]

            for i, elem in enumerate(_r):
                response.append("- {}\n".format(elem))

            response.append("\n\n_Send /support any time to send a question to a human._")

            update.message.reply_text("".join(response), reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True), parse_mode=ParseMode.MARKDOWN)

            return self.SELECTQUESTION
        else:
            update.message.reply_text("I didn't manage to find anything similiar in my database :( You can type /support to send a question to a human, or ask another question!", parse_mode=ParseMode.MARKDOWN)

            return None

    def selectQuestion(self, update, context):
        user = update.message.from_user
        self.logger.info("User %s selected \'%s\'", user.first_name, update.message.text)

        # If not in the list, go back to # question with a note saying you can use /support to send to human
        if update.message.text not in self.engine.datarows:
            update.message.reply_text("Hmm, I didn't manage to find '{}' in my database. Did you choose a question from the list above? If you would like to ask something else, could you try asking again?\n\n_If you would like to send the question to a human, type /support._".format(update.message.text), parse_mode=ParseMode.MARKDOWN)
        else:
            _r = self.engine.datarows[update.message.text]

            update.message.reply_text("{}\n\n{}\n\nHope that was helpful!\n\nIf you would like to send the question to a human instead, type /support. Otherwise, feel free to ask another question!".format(_r.question, _r.answer))

        return self.QUESTION

    def support(self, update, context):
        reply_keyboard = [['Yes', 'No']]

        user = update.message.from_user
        self.logger.info("User %s requested for support.", user.first_name)
        update.message.reply_text('Aw snap, would you like to send the question to our question bank? '
            'It will be answered in bulk at a later point in time. ',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

        return self.SUPPORTCONFIRM

    def supportConfirm(self, update, context):
        # Get user to type their question clearly and then use engine.add_to_questionbank

        user = update.message.from_user
        self.logger.info("Request for support %s: %s", user.first_name, update.message.text)

        if update.message.text == "Yes":
            update.message.reply_text('Righty, please type your question clearly and concisely in *1 message*. It will then be sent to my humans to be answered. '
            'You can send /skip if you would like to skip out.', parse_mode=ParseMode.MARKDOWN)

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
