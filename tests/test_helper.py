"""
===Description===
Module for testing all modules, except gui_export
-service - to test Lingualeo API for changes
-handler - to test handlers for correct work
-
"""
import unittest
from handler import Base, Kindle, Text, Input
from service import Lingualeo
from collections import Counter
import sqlite3
import os


def createKindleDatabase(db_name):
    """
    Create typical Kindle database with mastered and non-mastered words
    """
    array = [
        {
         'word_id': "en:even", 'lookups_id': 'CE',
         'word': "even", 'stem': "even",
         'category': 0, 'usage': "The integer is even"
        },
        {
         'word_id': "en:watched", 'lookups_id': 'WA',
         'word': "watch", 'stem': "watch",
         'category': 0, 'usage': "I've watched this show"
        },
        {
         'word_id': "en:nervous", 'lookups_id': 'NE',
         'word': "nervous", 'stem': "nervous",
         'category': 0, 'usage': "I'm nervous"
        },
        {
         'word_id': "en:guests", 'lookups_id': 'GU',
         'word': "guests", 'stem': "guest",
         'category': 100, 'usage': "I had a lot of guests there"
        },
        {
         'word_id': "en:doing", 'lookups_id': 'DO',
         'word': "doing", 'stem': "do",
         'category': 100, 'usage': "He enjoyed doing this"
        }
    ]
    words_create_command = """
        CREATE TABLE WORDS
        (id TEXT PRIMARY KEY NOT NULL,
            word TEXT,
            stem TEXT,
            lang TEXT,
            category INTEGER DEFAULT 0,
            timestamp INTEGER DEFAULT 0,
            profileid TEXT);
    """
    lookups_create_command = """
        CREATE TABLE LOOKUPS
        (id TEXT PRIMARY KEY NOT NULL,
            word_key TEXT,
            book_key TEXT,
            dict_key TEXT,
            pos TEXT,
            usage TEXT,
            timestamp INTEGER DEFAULT 0);
    """
    words_insert_command = """
        INSERT INTO "WORDS" VALUES
            (:id,
             :word,
             :stem,
             'en',
             :category,
             0,
             '')
    """
    lookups_insert_command = """
        INSERT INTO "LOOKUPS" VALUES
            (:id,
             :word_key,
             'book_key',
             '',
             'pos',
             :usage,
             0)
    """
    with sqlite3.connect(db_name) as conn:
        conn.execute(words_create_command)
        conn.execute(lookups_create_command)
        for row in array:
            conn.execute(words_insert_command,
                         {
                          'id': row['word_id'],
                          'word': row['word'],
                          'stem': row['stem'],
                          'category': row['category']
                         })
            conn.execute(lookups_insert_command,
                         {
                          'id': row['lookups_id'],
                          'word_key': row['word_id'],
                          'usage': row['usage']
                         })
    return array


def createTxtFile(txt_name):
    """
    Text file with 5 rows
    """
    array = ['even', 'watched', 'nervous', 'guests', 'doing']
    with open(txt_name, 'w') as f:
        for i in array:
            f.write(i+'\n')
    return array


class TestLingualeo(unittest.TestCase):
    """
    Ensure that Lingualeo API is still the same
    """


class TestKindleHandler(unittest.TestCase):
    """
    Ensure that Kindle handler returns expected result
    """
    TEST_DB = 'test.db'

    def setUp(self):
        """
        Create test database
        """
        if os.path.exists(self.TEST_DB):
            os.remove(self.TEST_DB)
        self.handler = Kindle(source=self.TEST_DB)
        self.array = createKindleDatabase(self.TEST_DB)
        self.new_words = Counter(i['category'] for i in self.array)[0]
        self.all_words = len(self.array)

    def tearDown(self):
        """
        Remove unneeded db
        """
        if os.path.exists(self.TEST_DB):
            os.remove(self.TEST_DB)

    def test_read_not_implemented(self):
        """
        Not overridden read() throws exception
        """
        b = Base(source='')
        with self.assertRaises(NotImplementedError):
            b.read()

    def test_only_new_words(self):
        """
        Reading test Kindle database with 'only_new_words' returns self.new_words
        """
        self.handler.read(only_new_words=True)
        words_count = len(self.handler.data)
        self.assertEqual(words_count, self.new_words)

    def test_all_words(self):
        """
        Reading test Kindle database by default returns self.all_words
        """
        self.handler.read()
        words_count = len(self.handler.data)
        self.assertEqual(words_count, self.all_words)


class TestTextHandler(unittest.TestCase):
    """
    Ensure that Text handler returns expected result
    """
    TEST_TXT = 'test.txt'

    def setUp(self):
        """
        Create txt file
        """
        if os.path.exists(self.TEST_TXT):
            os.remove(self.TEST_TXT)
        self.handler = Text(source=self.TEST_TXT)
        self.array = createTxtFile(self.TEST_TXT)
        self.words = len(self.array)

    def tearDown(self):
        """
        Remove test.txt
        """
        if os.path.exists(self.TEST_TXT):
            os.remove(self.TEST_TXT)

    def test_correct_count_of_text_words(self):
        """
        Reading tes.txt returns self.words_count
        """
        self.handler.read()
        words_count = len(self.handler.data)
        self.assertEqual(words_count, self.words)


class TestInputHandler(unittest.TestCase):
    """
    Ensure that Input handler returns expected result
    """
    TEST_WORD = 'test'

    def setUp(self):
        """
        Just for convention
        """
        self.handler = Input(source=self.TEST_WORD)

    def test_correct_word(self):
        """
        Data should have test word in it
        """
        self.handler.read()
        self.assertIn(self.handler.data, self.TEST_WORD)
