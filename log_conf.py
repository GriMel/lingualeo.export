# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for configuring logger
"""

import logging
from os.path import join


def setLogger(level=logging.DEBUG,
              name="my_logger",
              log_file=join("src", "log.out")):
    """
    Default logger for all classes/modules
    If not DEBUG - don't show to console anything.
    """
    DEBUG = False

    logger = logging.getLogger(name)
    logger.setLevel(level)

    ch = logging.StreamHandler()
    console_lvl = logging.DEBUG if DEBUG else logging.INFO
    ch.setLevel(console_lvl)
    formatter = logging.Formatter('%(message)s')
    ch.setFormatter(formatter)

    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s :: %(name)s - %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p')
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
