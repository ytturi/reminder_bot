from __future__ import annotations
from datetime import datetime
from enum import Enum
from reminderbot.conf import get_database
from typing import Any, Dict, Iterator, Tuple, TYPE_CHECKING
from logging import getLogger

from sqlalchemy import select, desc, asc
from telegram.ext import CommandHandler

from reminderbot.utils import (
    remove_command_message,
    send_typing_action,
    get_enabled_chat,
    escape_for_markdown_v2
)

if TYPE_CHECKING:
    from telegram import Update


logger = getLogger(__name__)


class DateFilter(Enum):
    no_filter = "NoFilter"
    past = "past"
    future = "next"


@send_typing_action
def next_event(update: Update, context) -> None:
    """
    Show the next 5 events in the database
    """
    logger.info("Handle 'next'")

    telegram_chat_id = update.message.chat.id
    telegram_chat_name = update.message.chat.title

    chat_id = get_enabled_chat(telegram_chat_id, telegram_chat_name)
    if chat_id is None:
        update_message = "This chat hasn't been allowed. Try /register_chat and send a message to the owner."
        update.message.reply_text(update_message)
        return

    update.message.reply_markdown_v2(
        generate_list_events(chat_id, 5, DateFilter.future)
    )


@send_typing_action
def last_event(update: Update, context) -> None:
    """
    Show the last 5 events in the database.
    """
    logger.info("Handle 'last'")

    telegram_chat_id = update.message.chat.id
    telegram_chat_name = update.message.chat.title

    chat_id = get_enabled_chat(telegram_chat_id, telegram_chat_name)
    if chat_id is None:
        update_message = "This chat hasn't been allowed. Try /register_chat and send a message to the owner."
        update.message.reply_text(update_message)
        return

    update.message.reply_text(
        generate_list_events(chat_id, 5, DateFilter.past), parse_mode="markdown"
    )


@send_typing_action
def list_events(update: Update, context) -> None:
    """
    List 10 events. By default it will be the next 10 events.
    Format:
    /list [next|past] <amount>

    Options are:

    - amount: integer
        amount of events to show
        Defaults to 10
        "all" is a special option to return all events

    - next: only show future events
        This option is not needed when listing future events without "all"
    - past: only show past events
    """
    logger.info("Handle 'update'")

    telegram_chat_id = float(update.message.chat.id)
    telegram_chat_name = update.message.chat.title

    chat_id = get_enabled_chat(telegram_chat_id, telegram_chat_name)
    if chat_id is None:
        update_message = "This chat hasn't been allowed. Try /register_chat and send a message to the owner."
        update.message.reply_text(update_message)
        return

    # Remove the first 6 characters: "/list "
    message_text = update.message.text[6:].strip()
    amount, date_filter = parse_list_arguments(message_text)

    update.message.reply_markdown_v2(
        generate_list_events(chat_id, amount, date_filter)
    )


def parse_list_arguments(message: str) -> Tuple[int, DateFilter]:
    """
    Parse the arguments of the "list" command

    Args:
        message (text): RAW text from the message (without the command)

    Returns:
        int: Amount of events to show.
            [0] - all
            [>0] - otherwise
        DateFilter: Which filter on the date to be applied
    """

    if not message:
        return 10, DateFilter.future

    args = message.split()

    # If only one arg it could be amount or date filter
    if len(args) == 1:
        arg = args[0]

        # Try to get amount
        try:
            amount = parse_list_amount(arg)
            # Future is the default when the amount is not 'all'
            if amount:
                return amount, DateFilter.future

            # Otherwise we don't want to filter
            else:
                return amount, DateFilter.no_filter

        # If it's not an amount, it has to be a date filter
        except ValueError:
            # 10 is the default amount
            return 10, DateFilter(arg)

    else:
        return parse_list_amount(args[0]), DateFilter(args[1])


def parse_list_amount(amount_str: str) -> int:
    """
    Convert str to absolute integer.

    If amount is "all", then it will be 0.

    Args:
        amount_str (str): amount from the message

    Returns:
        int: amount to be used
    """

    if amount_str.lower() == "all":
        return 0

    else:
        return abs(int(amount_str))


def generate_list_events(chat_id: int, amount: int, date_filter: DateFilter) -> str:
    """
    List the existing events for the current chat

    Args:
        chat_id (int): Chat requesting the list of events
        amount (int): Amount of events to retrieve (0=all)
        date_filter (DateFilter): Filter for the date

    Returns:
        str: Message to reply
    """

    amount_str = (str(amount) if amount else "All") + " "
    date_str = (date_filter.value + " ") if date_filter != DateFilter.no_filter else ""
    event_texts = [f"*{amount_str}{date_str}events:*\n"]

    events = list_events_db(chat_id=chat_id, amount=amount, date_filter=date_filter)
    for event in events:
        event_texts.append(
            f"-\[{event['date']}\] *{event['title']}* _\<{event['id']}\>_"
        )

    return escape_for_markdown_v2("\n".join(event_texts))


def list_events_db(
    chat_id: int, amount: int, date_filter: DateFilter
) -> Iterator[Dict[str, Any]]:
    """
    Query the database to retrieve the list of events of a singular chat.

    Returns the events as a generator.

    Args:
        chat_id (int): Chat requesting the list of events
        amount (int): Amount of events to retrieve (0=all)
        date_filter (DateFilter): Filter for the date

    Yields:
        Dict[str, Any]: Event from the database
    """
    from reminderbot.conf import get_database

    database = get_database()

    select_query = select(
        [database.reminder.c.id, database.reminder.c.date, database.reminder.c.title]
    ).where(database.reminder.c.chat_id == chat_id)

    if amount:
        select_query = select_query.limit(amount)

    if date_filter != DateFilter.no_filter:
        current_date = datetime.now()

        if date_filter == DateFilter.past:
            select_query = select_query.where(database.reminder.c.date < current_date)

        else:
            select_query = select_query.where(database.reminder.c.date > current_date)

    if date_filter == DateFilter.future:
        select_query.order_by(asc(database.reminder.c.date))

    else:
        select_query.order_by(desc(database.reminder.c.date))

    results = database.engine.execute(select_query)

    return ({**row} for row in results)


@send_typing_action
@remove_command_message
def pin_event(update: Update, context) -> None:
    """
    Show the data of the next event and pin the message
    """

    logger.info("Handle 'pin'")

    telegram_chat_id = update.message.chat.id
    telegram_chat_name = update.message.chat.title

    chat_id = get_enabled_chat(telegram_chat_id, telegram_chat_name)
    if chat_id is None:
        update_message = "This chat hasn't been allowed. Try /register_chat and send a message to the owner."
        update.message.reply_text(update_message)
        return

    event_message = get_event_message(chat_id=chat_id)
    if event_message:
        sent_message = update.message.reply_markdown_v2(event_message)
        sent_message.pin()


@send_typing_action
@remove_command_message
def show_event(update: Update, context) -> None:
    """
    Show the data of a single event
    """
    
    logger.info("Handle 'event'")

    telegram_chat_id = update.message.chat.id
    telegram_chat_name = update.message.chat.title

    chat_id = get_enabled_chat(telegram_chat_id, telegram_chat_name)
    if chat_id is None:
        update_message = "This chat hasn't been allowed. Try /register_chat and send a message to the owner."
        update.message.reply_text(update_message)
        return

    # Remove the first 6 characters: "/event"
    event_id = int(update.message.text[6:].strip())
    event_message = get_event_message(chat_id=chat_id, event_id=event_id)
    if event_message:
        update.message.reply_markdown_v2(event_message)
    
    else:
        update.message.reply_text("This event wasn't found. Try /list")


def get_event_message(chat_id: int, event_id: Optional[int] = None) -> str:
    """
    Generate the message for the event with `event_id`
    or the next event to happen for the chat.

    Args:
        chat_id (int): ID of the database chat
        event_id (Optional[int]): ID of the database event

    Returns:
        str: message to reply with markdown
    """

    event_data = get_event_data(chat_id=chat_id, event_id=event_id)
    
    if event_data is not None:
        event_message = f"_{event_data['date']}_\n*{event_data['title']}*\n\n{event_data['text']}"
        return escape_for_markdown_v2(event_message)
    
    else:
        return ''


def get_event_data(chat_id: int, event_id: Optional[int]) -> Optional[Dict[str,Any]]:
    """
    Get the data for a single event

    Args:
        chat_id (int): ID of the chat that the event should belong to
        event_id (Optional[int]): ID of the event. None if it should get the next event
    """

    database = get_database()

    select_query = (select([database.reminder.c.date, database.reminder.c.title ,database.reminder.c.text]).where(database.reminder.c.chat_id == chat_id))
    
    if event_id is None:
        current_date = datetime.now()
        select_query = (
            select_query.where(database.reminder.c.date > current_date)
            .order_by(asc(database.reminder.c.date))
            .limit(1)
        )

    else:
        select_query = select_query.where(database.reminder.c.id==event_id)

    result = database.engine.execute(select_query).first()

    if result is None:
        return None

    else:
        return {**result}


EVENTS_HANDLERS = [
    CommandHandler("next", next_event),
    CommandHandler("last", last_event),
    CommandHandler("list", list_events),
    CommandHandler("event", show_event),
    CommandHandler("pin", pin_event),
]
