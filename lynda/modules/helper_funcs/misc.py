# Taken from @ HarukaNetwork/HarukaAya
# Copyright (C) 2017-2019 Paul Larsen
# Copyright (C) 2019-2020 Akito Mizukito (Haruka Network Development)
# Give a Star to the source and Follow: https://gitlab.com/HarukaNetwork/OSS/HarukaAya


from typing import List, Dict
from telegram import MAX_MESSAGE_LENGTH, InlineKeyboardButton, ParseMode, Update
from telegram.error import TelegramError
from telegram.ext import CallbackContext

from lynda import NO_LOAD


class EqInlineKeyboardButton(InlineKeyboardButton):
    def __eq__(self, other):
        return self.text == other.text

    def __lt__(self, other):
        return self.text < other.text

    def __gt__(self, other):
        return self.text > other.text


def split_message(msg: str) -> List[str]:
    if len(msg) < MAX_MESSAGE_LENGTH:
        return [msg]

    lines = msg.splitlines(True)
    small_msg = ""
    result = []
    for line in lines:
        if len(small_msg) + len(line) < MAX_MESSAGE_LENGTH:
            small_msg += line
        else:
            result.append(small_msg)
            small_msg = line
        # Else statement at the end of the for loop, so append the leftover string.
        result.append(small_msg)

    return result


def paginate_modules(_page_n: int, module_dict: Dict, prefix, chat=None) -> List:
    if not chat:
        modules = sorted(
            [
                EqInlineKeyboardButton(
                    x.__mod_name__,
                    callback_data=f"{prefix}_module({x.__mod_name__.lower()})",
                )
                for x in module_dict.values()
            ]
        )
    else:
        modules = sorted(
            [
                EqInlineKeyboardButton(
                    x.__mod_name__,
                    callback_data=f"{prefix}_module({chat},{x.__mod_name__.lower()})",
                )
                for x in module_dict.values()
            ]
        )
    pairs = [
    modules[i * 3:(i + 1) * 3] for i in range((len(modules) + 3 - 1) // 3)
    ]
    round_num = len(modules) / 3
    calc = len(modules) - round(round_num)
    if calc in [1, 2]:
        pairs.append((modules[-1], ))
    return pairs


def send_to_list(context: CallbackContext, send_to: list, message: str, markdown=False, html=False) -> None:
    if html and markdown:
        raise Exception("Can only send with either markdown or HTML!")
    for user_id in set(send_to):
        try:
            if markdown:
                context.bot.send_message(user_id, message, parse_mode=ParseMode.MARKDOWN)
            elif html:
                context.bot.send_message(user_id, message, parse_mode=ParseMode.HTML)
            else:
                context.bot.send_message(user_id, message)
        except TelegramError:
            pass  # ignore users who fail


def build_keyboard(buttons):
    keyb = []
    for btn in buttons:
        if btn.same_line and keyb:
            keyb[-1].append(InlineKeyboardButton(btn.name, url=btn.url))
        else:
            keyb.append([InlineKeyboardButton(btn.name, url=btn.url)])

    return keyb


def revert_buttons(buttons):
    return "".join(
        f"\n[{btn.name}](buttonurl://{btn.url}:same)"
        if btn.same_line
        else f"\n[{btn.name}](buttonurl://{btn.url})"
        for btn in buttons
    )


def is_module_loaded(name):
    return name not in NO_LOAD

def sendMessage(text: str, context: CallbackContext, update: Update):
    return context.bot.send_message(update.message.chat_id,
                                    reply_to_message_id=update.message.message_id,
                                    text=text, parse_mode=ParseMode.HTML)
