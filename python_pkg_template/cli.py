# -*- coding: utf-8 -*-
# ------------------------------------------------------
# Author: Ytturi
# Author's e-mail: ytturi@protonmail.com
# Version: 0.1
# License: MIT
# ------------------------------------------------------
from logging import getLogger
import click

from python_pkg_template.confs import read_configs, init_logger


@click.command()
@click.option('-i', '--init', type=str, help='Initialize a demo Config File to use')
@click.option('-c', '--config-file', type=str, help='Config File to use')
@click.option('-v', '--verbose', type=str, help='Add verbosity to log (log-level INFO)')
@click.option('-d', '--debug', type=str, help='Set logger to DEBUG')
def do_smth(init, config_file, verbose, debug):
    if init:
        init_configs(config_file)
        exit(0)
    read_configs(config_file)
    init_logger(verbose, debug)
    logger = getLogger('INIT')
    logger.info('INITIALIZED')

if __name__ == '__main__':
    do_smth()
