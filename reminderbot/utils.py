###############################################################################
# Project: Mort de Gana Bot
# Authors:
# - Ytturi
# - gdalmau
# Descr: Utils for the bot
###############################################################################
from __future__ import annotations
from datetime import datetime
from functools import wraps
from random import randint, choice
from typing import Callable, Optional, Tuple, TYPE_CHECKING

from sqlalchemy import select, text
import telegram

from reminderbot.conf import get_debug_enabled, get_database

if TYPE_CHECKING:
    from telegram import User


def send_typing_action(func: Callable) -> Callable:
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=telegram.ChatAction.TYPING
        )
        return func(update, context, *args, **kwargs)

    return command_func


def remove_command_message(func: Callable) -> Callable:
    """Removes the message that triggered the handler."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        if get_debug_enabled():
            return func(update, context, *args, **kwargs)
        return_value = func(update, context, *args, **kwargs)
        # Try to remove the original message
        try:
            update.effective_message.delete()
        except:
            # It raises an exception if
            # - it's already removed
            # - it doesn't have permissions
            # But we don't care
            pass
        return return_value

    return command_func


def get_username(telegram_user: User) -> str:
    """
    Get the username from the telegram user

    Args:
        telegram_user (User): Telegram User

    Returns:
        str: Username if it has one. Public name otherwise
    """
    return telegram_user.username or telegram_user.full_name


def get_enabled_chat(chat_id: int, chat_name: str) -> Optional[int]:
    """
    Verify that the `chat_id` is registered in the database.

    If `chat_id` exists, also update the name if needed.

    Args:
        chat_id (int): chat_id from the telegram chat

    Returns:
        Optional[int]: ID of the chat when it exists, otherwise `None`
    """

    database = get_database()

    select_query = select([database.chat.c.id, database.chat.c.name]).where(
        database.chat.c.chat_id == chat_id
    )
    result = database.engine.execute(select_query).first()
    if result is not None:
        if result["name"] != chat_name:
            update_chat(result["id"], result["name"])

    return result["id"] if result is not None else None


def update_chat(chat_id: int, chat_name: str) -> None:
    """
    Update the chat name in the database

    Args:
        chat_id (int): ID of the chat (row ID)
        chat_name (str): [description]
    """

    update_query = text(
        """
        UPDATE chat SET name = :chat_name WHERE id = :chat_id
        """
    )

    database = get_database()
    database.engine.execute(update_query, chat_name=chat_name, chat_id=chat_id)


def parse_message_to_event(message_text: str) -> Tuple[datetime, str, str]:
    """
    Parse the message text into the three attributes of an event

    Args:
        message_text (str): Raw text of the message

    Returns:
        datetime: Time of the event
        str: Title of the event
        str: Description of the event
    """

    event_date_str, event_title, event_message = message_text.split("|", 3)
    event_date_str = event_date_str.strip()
    event_title = event_title.strip()
    event_message = event_message.strip()
    event_date = datetime.strptime(event_date_str, "%d-%m-%Y %H:%M")

    return event_date, event_title, event_message


def escape_for_markdown_v2(message: str) -> str:
    """
    Escape a message so it can be sent with markdown_v2

    Args:
        message (str): Message without escaped characters

    Returns:
        str: Message with escaped characters
    """

    return (
        message.replace('-', '\-')
        .replace('!', '\!')
        .replace('.', '\.')
        .replace('[', '\[')
        .replace(']', '\]')
        .replace('(', '\(')
        .replace(')', '\)')
    )