#!/usr/bin/env python
# -*- coding: utf-8 -*-
from config import sources
import sqlite3

database = sources.get('kindle')

conn = sqlite3.connect(database)
with conn:
    conn.execute("DELETE FROM WORDS;")
    conn.execute("DELETE FROM LOOKUPS;")
    conn.execute("UPDATE METADATA SET sscnt = 0 WHERE id in ('WORDS', 'LOOKUPS');")
    conn.commit()
    print("Database cleared")