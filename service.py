#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import urllib.request as urllib2
import json
from http.cookiejar import CookieJar


class Lingualeo:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.cj = CookieJar()

    def auth(self):
        url = "http://api.lingualeo.com/api/login"
        values = {
            "email": self.email,
            "password": self.password
        }

        return self.get_content(url, values)

    def add_word(self, word, tword):
        url = "http://api.lingualeo.com/addword"
        values = {
            "word": word,
            "tword": tword,
            "context":"Silly"
        }
        self.get_content(url, values)

    def get_translates(self, word):
        url = "http://api.lingualeo.com/gettranslates?word=" + urllib.parse.quote_plus(word)

        try:
            result = self.get_content(url, {})
            translate = result["translate"][0]
            return {
                "is_exist": translate["is_user"],
                "word": word,
                "tword": translate["value"].encode("utf-8")
            }
        except Exception as e:
            return e.message

    def get_content(self, url, values):
        data = urllib.parse.urlencode(values).encode('utf-8')
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        req = opener.open(url, data)

        return json.loads(req.read().decode('utf-8'))
