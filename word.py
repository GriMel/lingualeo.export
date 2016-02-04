import sqlite3
import pysrt
import re


class Base(object):
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
    def read(self, only_new_words=False):
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
        for row in conn.execute(command):
            self.data.append({'word': row[0], 'context': row[1]})
        conn.close()


class Text(Base):
    def read(self):
        with open(self.source, "r") as f:
            for line in f:
                self.data.append({'word': line})


class Input(Base):
    def read(self):
        self.data = self.source


class Subs(Base):
    def read(self):
        allwords=list()
        subs = pysrt.open(self.source[0])
        for sub in subs:
            text=sub.text
            text=re.sub('<[^<]+?>', '', text)
            chars=[",",".","!","?","»","«","=","—","_","@","--","(",")",":"]
            for ch in chars:
                text=text.replace(ch,"")
            words = text.split()
            for word in words:
                if word != "-":
                    if word not in allwords:
                        self.data.append({'word': word, 'context': text})

            allwords=allwords + words
