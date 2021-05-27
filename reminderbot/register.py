from __future__ import annotations
from datetime import datetime
from reminderbot.conf import get_database
from typing import TYPE_CHECKING
from logging import getLogger

from telegram.ext import CommandHandler

from reminderbot.utils import remove_command_message, send_typing_action, get_enabled_chat

if TYPE_CHECKING:
    from telegram import Update


logger = getLogger(__name__)


@send_typing_action
def register_chat(update: Update, context) -> None:
    logger.info("Handle 'register_chat'")
    chat = update.message.chat
    chat_id = chat.id
    chat_name = chat.title
    logger.info(f"Register\nID: {chat_id}\nNAME: '{chat_name}'")
    update.message.reply_text(f"'{chat_name}' may be registered Soon\u2122")


#@remove_command_message
@send_typing_action
def register_event(update: Update, context) -> None:
    logger.info("Handle 'register'")
    
    telegram_chat_id = update.message.chat.id
    telegram_chat_name = update.message.chat.title

    chat_id = get_enabled_chat(telegram_chat_id, telegram_chat_name)

    if chat_id is not None:
        # We need to ignore the first 10 characters which are "/register "
        message_text = update.message.text[10:]
        try:
            event_date_str, event_title, event_message = message_text.split('|', 3)
            event_date_str = event_date_str.strip()
            event_title = event_title.strip()
            event_message = event_message.strip()
            event_date = datetime.strptime(event_date_str, '%d-%m-%Y %H:%M')
            register_event_db(
                chat_id=chat_id,
                date=event_date,
                title=event_title,
                message=event_message
            )
            update_message = f"Registered:\nTitle: {event_title}\nDate:{event_date}\nMessage:\n{event_message}"

        except Exception as err:
            update_message = "Could not process the event. Should have the format: '/register <date (dd-mm-yyyy HH:MM)>|<title>|<message>'"
            logger.error(update_message)
            logger.error(f"Exception: {err}")
            logger.error(f"Message:\n{update.message.text}")
    
    else:
        update_message = "This chat hasn't been allowed. Try /register_chat and send a message to the owner."

    update.message.reply_text(update_message)


def register_event_db(chat_id: int, date: datetime, title: str, message: str) -> None:
    """
    Register the event in the database

    Args:
        chat_id (int): ID of the chat (database)
        date (datetime): [description]
        title (str): [description]
        message (str): [description]
    """

    database = get_database()
    
    insert_values = {
        'chat_id': chat_id,
        'title': title,
        'date': date,
        'text': message
    }
    insert_query = database.reminder.insert().values(insert_values)
    database.engine.execute(insert_query)


REGISTER_HANDLERS = [
    CommandHandler("register_chat", register_chat),
    CommandHandler("register", register_event)
]