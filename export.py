#!/usr/bin/env python
# -*- coding: utf-8 -*-
from word import Kindle, Text, Input
from config import sources, auth
from service import Lingualeo
import sys
import traceback

email = config.auth.get('email')
password = config.auth.get('password')

try:
    export_type = sys.argv[1]
    if export_type == 'text':
        handler = Text(sources.get('text'))
    elif export_type == 'kindle':
        handler = Kindle(sources.get('kindle'))
    elif export_type == 'input' :
        handler = Input(sys.argv[2:])
    else:
        raise Exception('unsupported type')

    handler.read()

    lingualeo = Lingualeo(email, password)
    lingualeo.auth()

    for word, context in handler.get():
        word = word.lower()
        translate = lingualeo.get_translates(word)

        lingualeo.add_word(translate["word"], translate["tword"], context)
        print(translate)
        if not translate["is_exist"]:
            result = "Add word: "
        else:
            result = "Already exists: "

        result = result + word
        print (result)


except Exception:
    print (sys.exc_info())
    print(traceback.format_exc())