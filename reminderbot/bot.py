###############################################################################
# Project: Mort de Gana Bot
# Authors:
# - Ytturi
# - gdalmau
# Descr: Telegram bot initializer
###############################################################################
from __future__ import annotations
from telegram.ext import Updater
import logging
import click

# Self-imports
from reminderbot.conf import (
    read_configs,
    init_configs,
    init_logger,
    get_telegram_token,
    get_debug_enabled,
    get_database,
)
from reminderbot import HANDLERS


@click.command()
@click.option("-c", "--config", type=str, help="Use config file")
@click.option(
    "-i",
    "--init-config",
    "init_config",
    is_flag=True,
    default=False,
    help="Initialize config file",
)
@click.option(
    "--init_db", is_flag=True, default=False, help="Initialize the database and exit"
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Override verbosity level for the logger to INFO",
)
@click.option(
    "-d",
    "--debug",
    is_flag=True,
    default=False,
    help="Override verbosity level for the logger to DEBUG",
)
@click.option(
    "-t",
    "--token",
    default=False,
    help="Set telegram token instead of using a config file",
)
def listener(config, init_config, init_db, verbose, debug, token) -> None:
    # Init configs
    read_configs(config)

    # Init logger
    init_logger(verbose, debug)
    logger = logging.getLogger("INIT")

    # Init Configs
    if init_config:
        init_configs(config)
        logger.info("The file 'reminderbot.cfg' has been created.")
        exit(-1)

    # Init database
    database = get_database()
    if database.enabled:
        logger.info("Using database")

        if init_db is True:
            logger.info("Initializing database")
            database.init_database()

            exit(0)

    # Init listener
    if token:
        TOKEN = token
    else:
        TOKEN = get_telegram_token()
    if not TOKEN:
        logger.critical(
            "No token provided! Add a token at the config file: '~/.reminderbot.cfg'"
        )
        exit(-1)
    logger.debug("TOKEN: {}".format(TOKEN))
    updater = Updater(TOKEN, use_context=True)
    
    #   ADD Handlers
    debug_enabled = get_debug_enabled()
    logger.debug(f"Debug enabled: {debug_enabled}")
    for handler in HANDLERS:
        if debug_enabled and hasattr(handler, "command"):
            handler.command = [c + "_test" for c in handler.command]
        updater.dispatcher.add_handler(handler)

    #   Listen till end
    logger.info("ReminderBot has started!")
    try:
        updater.start_polling()
        updater.idle()
    finally:
        logger.info("Shutting down\nBot is going to sleep (...)\nNo more reminders today (...)\nZzz")


# Main Process
if __name__ == "__main__":
    listener()
