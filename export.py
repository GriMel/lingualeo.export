#!/usr/bin/env python
# -*- coding: utf-8 -*-
from word import Kindle, Text, Input, Subs
from config import sources, auth
from service import Lingualeo
import sys
import traceback

email = auth.get('email')
password = auth.get('password')

try:
    export_type = sys.argv[1]
    if export_type == 'text':
        if len(sys.argv) == 3:
            source = sys.argv[2]
        else:
            source = sources.get('text')
        handler = Text(source)
    elif export_type == 'kindle':
        handler = Kindle(sources.get('kindle'))
    elif export_type == 'input':
        handler = Input(sys.argv[2:])
    elif export_type == 'subs':
        handler = Subs(sys.argv[2:])
    else:
        raise Exception('unsupported type')

    handler.read()

    lingualeo = Lingualeo(email, password)
    lingualeo.auth()
    exist = 0
    added = 0
    print(len(handler.get()))
    for row in handler.get():
        word = row.get('word').lower()
        context = row.get('context', '')
        translate = lingualeo.get_translate(word)

        lingualeo.add_word(translate["word"], translate["tword"], context)
        if not translate["is_exist"]:
            result = "Added word: "
            added += 1
        else:
            result = "Already exists: "
            exist += 1
        result = result + word
        print (result)

    print("There were {} words.\n{} added, {} exist.".format(added+exist,
                                                             added,
                                                             exist))


except Exception:
    print (sys.exc_info())
    print(traceback.format_exc())
