# -*- coding: utf-8 -*-
# ------------------------------------------------------
# Author: Ytturi
# Author's e-mail: ytturi@protonmail.com
# Version: 0.1
# License: MIT
# ------------------------------------------------------
from subprocess import Popen, PIPE
from os import rename
import click

@click.command()
@click.argument('name')
def rename_pkg(name):
    """Change the template name from the package name in setup"""
    # Get pkg name from setup
    with open('setup.py', 'r') as setupfile:
        setuptxt = setupfile.readlines()
    pkgname = [x for x in setuptxt if "name='" in x][0]
    # Get name from line
    pkgname = pkgname.split("name='")[-1].strip()[:-2]
    # Rename pkg folder
    rename(pkgname, name)
    # Rename instances in files
    #TODO
    # Rename pkg in setup
    with open('setup.py', 'w') as setupfile:
        for line in setuptxt:
            setupfile.write('{}\n'.format(
                line.replace(pkgname, name)
            ))


if __name__ == "__main__":
    rename_pkg()
