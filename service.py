#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests

LOGIN = "http://api.lingualeo.com/api/login"
ADD_WORD = "http://api.lingualeo.com/addword"
GET_TRANSLATE = "http://api.lingualeo.com/gettranslates?word="


class Lingualeo(object):
    """Lingualeo.com API class"""
    TIMEOUT = 5

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.initUser()

    def initUser(self):
        self.cookies = None
        self.premium = None
        self.meatballs = None
        self.avatar = None
        self.fname = None
        self.lvl = None

    def auth(self):
        """authorization on lingualeo.com"""
        url = LOGIN
        values = {
            "email": self.email,
            "password": self.password
        }
        r = requests.get(url, values, timeout=self.TIMEOUT)
        self.cookies = r.cookies
        content = r.json()['user']
        self.premium = bool(content['premium_type'])
        if not self.premium:
            self.meatballs = content['meatballs']
        else:
            self.meatballs = "Unlimited"
        self.fname = content['fullname']
        self.avatar = requests.get(content['avatar_mini']).content
        self.lvl = content['xp_level']

    def get_translate(self, word):
        """get translation from lingualeo's API"""
        url = GET_TRANSLATE + word
        try:
            r = requests.get(url, cookies=self.cookies, timeout=self.TIMEOUT)
            translate = r.json()['translate'][0]
            tword = translate['value']
            is_exist = translate['is_user']
            return {
                "is_exist": is_exist,
                "word": word,
                "tword": tword
            }
        except (IndexError, KeyError):
            return {"is_exist": 0,
                    "word": word,
                    "tword": "No translation"}

    def add_word(self, word, tword, context=""):
        """add new word"""
        url = ADD_WORD
        values = {
            "word": word,
            "tword": tword,
            "context": context
        }
        requests.post(url, values, cookies=self.cookies, timeout=self.TIMEOUT)

    def isPremium(self):
        """tells if user has a premium status"""
        return self.premium

    def substractMeatballs(self):
        """method for substracting meatballs"""
        self.meatballs -= 1
