#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===Description===
Module for configuring Lingualeo API
"""

import requests
from operator import itemgetter
from collections import Counter


class Lingualeo(object):
    """Lingualeo.com API class"""

    TIMEOUT = 5
    LOGIN = "http://api.lingualeo.com/api/login"
    ADD_WORD = "http://api.lingualeo.com/addword"
    ADD_WORD_MULTI = "http://api.lingualeo.com/addwords"
    GET_TRANSLATE = "http://api.lingualeo.com/gettranslates?word="

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.auth_info = None
        self.cookies = None
        self.premium = None
        self.meatballs = None
        self.avatar = None
        self.fname = None
        self.lvl = None

    def initUser(self):
        
        self.premium = self.auth_info['premium_type']
        self.fname = self.auth_info['fullname']
        self.lvl = self.auth_info['xp_level']
        if not self.premium:
            self.meatballs = self.auth_info['meatballs']
        else:
            self.meatballs = "∞"
        try:
            self.avatar = requests.get(self.auth_info['avatar_mini'],
                                       timeout=self.TIMEOUT).content
        except:
            self.avatar = None

    def auth(self):
        """authorization on lingualeo.com"""
        url = self.LOGIN
        values = {
            "email": self.email,
            "password": self.password
        }
        r = requests.get(url, values, timeout=self.TIMEOUT)
        self.cookies = r.cookies
        self.auth_info = r.json()['user']

    def get_translate(self, word):
        """get translation from lingualeo's API"""
        url = self.GET_TRANSLATE + word
        try:
            response = requests.get(url,
                                    cookies=self.cookies,
                                    timeout=self.TIMEOUT)
            translate_list = response.json()['translate']
            translate_list = sorted(translate_list,
                                    key=itemgetter('votes'),
                                    reverse=True)
            translate = translate_list[0]
            tword = translate['value']
            is_exist = bool(translate['is_user'])
            if not is_exist:
                counter = Counter(i['is_user'] for i in translate_list)
                if counter.get(1, 0) > 0:
                    is_exist = True
            return {
                "is_exist": is_exist,
                "word": word,
                "tword": tword
            }
        except (IndexError, KeyError):
            return {"is_exist": False,
                    "word": word,
                    "tword": ""}

    def add_word(self, word, tword, context=""):
        """add new word"""
        url = self.ADD_WORD
        values = {
            "word": word,
            "tword": tword,
            "context": context
        }
        return requests.post(url,
                             values,
                             cookies=self.cookies,
                             timeout=self.TIMEOUT)

    def add_word_multiple(self, array):
        """add the array of words"""
        url = self.ADD_WORD_MULTI
        data = dict()
        for index, i in enumerate(array):
            data["words["+index+"][word]"] = array['word']
            data["words["+index+"][tword]"] = array['tword']
            data["words["+index+"][context]"] = array['context']

        return requests.post(url,
                             data,
                             cookies=self.cookies)

    def isPremium(self):
        """tells if user has a premium status"""
        return self.premium

    def substractMeatballs(self):
        """method for substracting meatballs"""
        self.meatballs -= 1

    def isEnoughMeatballs(self, words):
        """check if meatballs > words"""
        if not self.isPremium() and self.meatballs < words:
            return False
        else:
            return True
