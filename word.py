import sqlite3


class Base(object):
    data = []
    context = []

    def __init__(self, source):
        self.source = source

    def get(self):
        return self.data

    def read(self):
        raise NotImplementedError('Not implemented yet')

class Kindle(Base):
    def read(self):
        conn = sqlite3.connect(self.source)
        for row in conn.execute('SELECT WORDS.word, LOOKUPS.usage FROM WORDS INNER JOIN LOOKUPS ON WORDS.id = LOOKUPS.word_key LIMIT 20'):
            self.data.append({'word':row[0], 'context':row[1]})
        conn.close()
    


class Text(Base):
    def read(self):
        with open(self.source, "r") as f:
            self.data.append({'word':f.readline()})
            
class Input(Base):
    def read(self):
        self.data = self.source
