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
import json

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

    EMAIL = "b346059@trbvn.com"
    PASSWORD = "1234567890"
    TEST_AUTH_INFO = {'address': 'Ukraine, Kyyiv, Kiev',
        'age': 16,
        'autologin_key': 'd3c12598553e65d50ba52e1abcb5c705',
        'avatar': 'https://d144fqpiyasmrr.cloudfront.net/up'\
                  'loads/avatar/0.png',
        'avatar_mini': 'https://d144fqpiyasmrr.cloudfront.ne'\
                 't/uploads/avatar/0s100.png',
        'birth': '2000-01-01',
        'create_at': '2016-02-19 20:33:54',
        'daily_hours': 1,
        'denied_services': [],
        'fname': '',
        'fullname': 'b346059',
        'hungry_max_points': 150,
        'hungry_pct': 0,
        'hungry_points': 0,
        'is_gold': False,
        'lang_interface': 'ru',
        'lang_native': 'ru',
        'langlevel': 1,
        'leo_pic_url': 'http://d29idiqnj27ux5.cloudfront.net'\
                       '/8ac94ea62/images/tasks-leo-2.png',
        'meatballs': 200,
        'nickname': 'b346059',
        'port_version': '1.6.1',
        'premium_type': 0,
        'premium_until': '',
        'refcode': '9em5gg',
        'sex': 1,
        'sname': '',
        'user_id': 13720532,
        'words_cnt': 30,
        'words_known': 0,
        'xp_level': 1,
        'xp_max_points': 25,
        'xp_min_points': 0,
        'xp_points': 0,
        'xp_title': 'Ловкий новичок'}
    TEST_ADD_INFO = {'added_translate_count': 0,
                     'error_msg': '',
                     'from_syntrans_id': None,
                     'is_new': 0,
                     'is_user_word_created': 0,
                     'lang': {'current': 'ru', 'target': 'en'},
                     'lemmas': [{'lemma_id': 5756,
                     'lemma_value': 'BOOK',
                     'speech_part': {
                        'code': 'Adjective',
                        'name': 'прилагательное',
                        'short_name': 'прил.'
                        },
                    'speech_part_id': 1},
                    {
                        'lemma_id': 5756,
                        'lemma_value': 'BOOK',
                        'speech_part': {
                            'code': 'Noun',
                            'name': 'существительное',
                            'short_name': 'сущ.'
                            },
                    'speech_part_id': 7},
                    {
                        'lemma_id': 5756,
                        'lemma_value': 'BOOK',
                        'speech_part': {
                            'code': 'Verb',
                            'name': 'глагол',
                            'short_name': 'глаг.'
                            },
                    'speech_part_id': 12}],
                    'sound_url': 'http://d2x1jgnvxlnz25.'\
                                 'cloudfront.net/v2/3/5756-631152008.mp3',
                    'speech_part_id': 0,
                    'to_syntrans_id': None,
                    'translate_auto': 0,
                    'translate_id': 201656,
                    'translate_value': 'книга',
                    'word_id': 5756,
                    'word_rank': 318585,
                    'word_speech_parts': {
                        '1': {
                            'code': 'Adjective',
                            'name': 'прилагательное',
                            'short_name': 'прил.'
                            },
                        '12': {
                            'code': 'Verb',
                            'name': 'глагол',
                            'short_name': 'глаг.'
                            },
                        '7': {
                            'code': 'Noun',
                            'name': 'существительное',
                            'short_name': 'сущ.'}},
                    'word_top': 1,
                    'word_type': 1,
                    'word_user_cdate': 1455914074,
                    'word_value': 'book'}

    TEST_WORD_EXISTS = "book"
    TEST_TWORD_EXISTS = "книга"
    TEST_TWORD_EXISTS_TWO = "бронировать"
    TEST_WORD_NON_EXISTS = "zecrvt"

    def setUp(self):
        """
        Authenticate test user
        """
        self.lingualeo = Lingualeo(self.EMAIL, self.PASSWORD)
        self.lingualeo.auth()
        self.maxDiff = None

    def test_typical_auth_info(self):
        """
        Auth_info is equal to test auth info
        """
        self.assertEqual(self.lingualeo.auth_info, self.TEST_AUTH_INFO)

    def test_typical_get_translation_info(self):
        """
        Function get_translate returns predicted results
        """
        result = self.lingualeo.get_translate(self.TEST_WORD_EXISTS)
        # Dictionary on Lingualeo has 'бронировать' for 'book' 
        # The most popular translation, though, is 'книга'
        self.assertEqual(result,
                         {'is_exist': True,
                          'word':"book",
                          'tword': self.TEST_TWORD_EXISTS})
        result = self.lingualeo.get_translate(self.TEST_WORD_NON_EXISTS)
        self.assertEqual(result,
                         {'is_exist': False,
                          'word':"zecrvt",
                          'tword': ""})

    def test_typical_add_word_info(self):
        """
        Function add_word returns predicted results
        """
        response = self.lingualeo.add_word(self.TEST_WORD_EXISTS,
                                                self.TEST_TWORD_EXISTS)
        add_word_info = response.json()
        self.assertEqual(self.TEST_ADD_INFO, add_word_info)

    def test_init_info(self):
        """
        Test user has no premium status
        """
        self.lingualeo.initUser()
        self.assertEqual(self.lingualeo.premium, 0)
        self.assertEqual(self.lingualeo.fname, 'b346059')
        self.assertEqual(self.lingualeo.lvl, 1)
        self.assertEqual(self.lingualeo.meatballs, 200)

    def test_enough_meatballs(self):
        """
        Meatballs < words returns False
        """
        self.lingualeo.initUser()
        result = self.lingualeo.isEnoughMeatballs(201)
        self.assertEqual(result, False)

    def test_avatar_exception(self):
        """
        If no avatar - avatar is set to None
        """
        self.lingualeo.TIMEOUT = 0.01
        self.lingualeo.initUser()
        self.assertEqual(self.lingualeo.avatar, None)



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
