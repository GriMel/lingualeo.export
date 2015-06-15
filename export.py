#!/usr/bin/env python
# -*- coding: utf-8 -*-
import word
import config
import service
import sys
import traceback

email = config.auth.get('email')
password = config.auth.get('password')

try:
    export_type = sys.argv[1]
    if export_type == 'text':
        handler = word.Text(config.sources.get('text'))
    elif export_type == 'kindle':
        handler = word.Kindle(config.sources.get('kindle'))
    elif export_type == 'input' :
        handler = word.Input(sys.argv[2:])
    else:
        raise Exception('unsupported type')

    handler.read()

    lingualeo = service.Lingualeo(email, password)
    lingualeo.auth()

    for word in handler.get():
        word = word.lower()
        translate = lingualeo.get_translates(word)

        lingualeo.add_word(translate["word"], translate["tword"])
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