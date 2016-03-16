# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===Description===
Module for configuring handlers.
Every handler converts its input to self.data

Kindle - from Kindle db.
Text - from txt file.
Input - from manual input
"""

import sqlite3


class Base(object):
    """
    Base class for all handlers.
    """
    data = []
    context = []

    def __init__(self, source):
        self.source = source
        self.data = []

    def get(self):
        return self.data

    def read(self):
        raise NotImplementedError('Not implemented yet')


class Kindle(Base):
    """
    Handler of Kindle's database
    """

    def read(self, only_new_words=False):
        """
        Reading data from database.
        All words - category = 100.
        New words - category = 0.
        """
        conn = sqlite3.connect(self.source)
        command = None
        if only_new_words:
            command = "SELECT WORDS.stem, LOOKUPS.usage \
                        FROM WORDS INNER JOIN LOOKUPS ON \
                            WORDS.id = LOOKUPS.word_key \
                                WHERE \
                                    WORDS.lang = 'en' AND \
                                        WORDS.category = 0"
        else:
            command = "SELECT WORDS.stem, LOOKUPS.usage \
                        FROM WORDS INNER JOIN LOOKUPS ON \
                            WORDS.id = LOOKUPS.word_key \
                                WHERE \
                                    WORDS.lang = 'en'"
        for word, context in conn.execute(command):
            self.data.append({'word': word, 'context': context})
        conn.close()


class Text(Base):
    """
    Class for getting words from txt file.
    """

    def read(self):
        """
        Proceed every line of file.
        One line - one word.
        """
        with open(self.source, "r") as f:
            for line in f:
                self.data.append({'word': line.rstrip('\n')})


class Input(Base):
    """
    Class for getting word from input.
    """

    def read(self):
        """
        Given word = array.
        """
        self.data = self.source
