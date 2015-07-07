import sqlite3


class Base(object):
    data = []
    context = []

    def __init__(self, source):
        self.source = source

    def get(self):
        return zip(self.data, self.context)

    def read(self):
        raise NotImplementedError('Not implemented yet')


class Kindle(Base):
    def read(self):
        conn = sqlite3.connect(self.source)
        for row in conn.execute('SELECT word FROM WORDS;'):
            self.data.append(row[0])
        for row in conn.execure('SELECT stem from WORDS;'):
            self.context.append(row[0])
        conn.close()


class Text(Base):
    def read(self):
        with open(self.source, "r") as f:
            self.data.append(f.readline())
            self.context.append('')
            
class Input(Base):
    def read(self):
        self.data = self.source
