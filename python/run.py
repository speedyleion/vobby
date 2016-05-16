#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Temp file for launching twisted from command line.
Not liking this
"""
from twisted.scripts.twistd import run
from sys import argv
import os

def main():
    argv[1:] = ['-y', os.path.join(os.path.dirname(__file__), 'vobby.py')]

    run()

if __name__ == "__main__":
    main()
