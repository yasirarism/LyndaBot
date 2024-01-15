# AI module using Intellivoid's Coffeehouse API by @TheRealPhoenix
from time import time, sleep

from coffeehouse.lydia import LydiaAI
from coffeehouse.api import API
from coffeehouse.exception import CoffeeHouseError as CFError

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async, CallbackContext
from telegram.error import BadRequest, Unauthorized, RetryAfter

from lynda import dispatcher, AI_API_KEY, OWNER_ID
import lynda.modules.sql.chatbot_sql as sql
from lynda.modules.helper_funcs.chat_status import user_admin
from lynda.modules.helper_funcs.filters import CustomFilters

CoffeeHouseAPI = API(AI_API_KEY)
api_client = LydiaAI(CoffeeHouseAPI)


@run_async
@user_admin
def add_chat(update: Update, _):
    global api_client
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if is_chat := sql.is_chat(chat_id):
        msg.reply_text("AI is already enabled for this chat!")
    else:
        ses = api_client.create_session()
        sql.set_ses(chat_id, str(ses.id), str(ses.expires))
        msg.reply_text("AI successfully enabled for this chat!")


@run_async
@user_admin
def remove_chat(update: Update, _):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if is_chat := sql.is_chat(chat_id):
        sql.rem_chat(chat_id)
        msg.reply_text("AI disabled successfully!")
    else:
        msg.reply_text("AI isn't enabled here in the first place!")


def check_message(context: CallbackContext, message):
    reply_msg = message.reply_to_message
    if message.text.lower() == "lynda":
        return True
    if reply_msg:
        if reply_msg.from_user.id == context.bot.get_me().id:
            return True
    else:
        return False


@run_async
def chatbot(update: Update, context: CallbackContext):
    global api_client
    msg = update.effective_message
    chat_id = update.effective_chat.id
    is_chat = sql.is_chat(chat_id)
    if not is_chat:
        return
    if msg.text and not msg.document:
        if not check_message(context.bot, msg):
            return
        sesh, exp = sql.get_ses(chat_id)
        query = msg.text
        try:
            if int(exp) < time():
                ses = api_client.create_session()
                ses_id = str(ses.id)
                expires = str(ses.expires)
                sql.set_ses(chat_id, ses_id, expires)
                sesh, exp = sql.get_ses(chat_id)
        except ValueError:
            pass
        try:
            context.bot.send_chat_action(chat_id, action='typing')
            rep = api_client.think_thought(sesh, query)
            sleep(0.3)
            msg.reply_text(rep, timeout=60)
        except CFError as e:
            context.bot.send_message(
                OWNER_ID, f"Chatbot error: {e} occurred in {chat_id}!")


@run_async
def list_chatbot(update: Update, context: CallbackContext):
    chats = sql.get_all_chats()
    text = "<b>AI-Enabled Chats</b>\n"
    for chat in chats:
        try:
            x = context.bot.get_chat(int(*chat))
            name = x.title if x.title else x.first_name
            text += f"• <code>{name}</code>\n"
        except (BadRequest, Unauthorized):
            sql.rem_chat(*chat)
        except RetryAfter as e:
            sleep(e.retry_after)
    update.effective_message.reply_text(text, parse_mode="HTML")


__mod_name__ = "Chatbot"

__help__ = """
Chatbot utilizes the CoffeeHouse API and allows Lynda to talk back making your chat more interactive.
This is an ongoing upgrade and is only available in your chats if you reach out to @YorktownEagleUnion and ask for it.
In future we might make it open for any chat and controllable by group admins.
Powered by CoffeeHouse (https://coffeehouse.intellivoid.net/) from @Intellivoid

──「 *Commands* 」──
->  `/addchat`
Enables Chatbot mode in the chat.
-> `/rmchat`
Disables Chatbot mode in the chat.

──「 *Nation Level Required:* 」──
-> `/listai`
Lists the chats the chatmode is enabled in.
"""

ADD_CHAT_HANDLER = CommandHandler("addchat", add_chat)
REMOVE_CHAT_HANDLER = CommandHandler("rmchat", remove_chat)
CHATBOT_HANDLER = MessageHandler(Filters.text & (~Filters.regex(
    r"^#[^\s]+") & ~Filters.regex(r"^!") & ~Filters.regex(r"^s\/")), chatbot)
CHATBOTLIST_HANDLER = CommandHandler("listai", list_chatbot, filters=CustomFilters.dev_filter)
# Filters for ignoring #note messages, !commands and sed.

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(REMOVE_CHAT_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)
dispatcher.add_handler(CHATBOTLIST_HANDLER)
