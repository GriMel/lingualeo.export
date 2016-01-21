# !/usr/bin/env python
import logging
from os.path import join


def setLogger(level=logging.DEBUG,
              name="my_logger",
              file=join("src", "log.out")):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    ch.setFormatter(formatter)

    fh = logging.FileHandler(file)
    fh.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s : %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p')
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
