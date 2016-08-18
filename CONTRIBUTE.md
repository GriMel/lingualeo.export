## Requirements
* Python 3
* PyQt4
* ```pip3 install -r requirements.txt```

## To run
* ```python gui_export.py```

## To compile
* Install pyinstaller

```python compile.py <version>```

example

```python compile.py 0.10.0```

## To add translations
* Install PyQt4 Linguist
* qm files located in src/lang
* Automated script
```
python language.py ts ua  # to get qt_ua.ts editable file
python language.py qm ua  # to create qt_ua.qm from qt_ua.ts
```
