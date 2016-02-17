# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===Description===
Module for compiling by pyinstaller to
executable file (Linux or Windows)

===Usage===
python compile.py <version>

for version 1.0.1:
    python compile.py 1.0.1
"""
import argparse
import os
import shutil
import json


def compile_script(folderName):
    """
    Main script.
    Sets folder, icon and runs pyinstaller
    """
    icon = os.path.join("src", "pics", "lingualeo.ico")
    name = "Kindleo"
    scriptName = "gui_export.py"
    command = "pyinstaller --noconsole -F --icon={0} --name={1} "\
              "--distpath={2} {3}".format(icon,
                                          name,
                                          folderName,
                                          scriptName)
    os.system(command)
    print("Compiled to {}".format(folderName))


def copytree(src, dst):
    """
    Copy folder/file.
    """
    if os.name == 'nt':
        ignored_folders = ['sqlite_lin']
    elif os.name == 'posix':
        ignored_folders = ['sqlite_win']
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, src, item)
        if os.path.isdir(s):
            if any(w in s for w in ignored_folders):
                continue
            else:
                shutil.copytree(s, d)
        else:
            # to ignore src.ini
            continue
    print("Copied src folder")


def change_json(version):
    """
    Change version's field in json file.
    """
    data_file = os.path.join("src", "data", "data.json")
    with open(data_file) as f:
        data_info = json.loads(f.read())
    data_info['version'] = version
    with open(data_file, "w+") as f:
        f.write(json.dumps(data_info))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    args = parser.parse_args()
    version = args.version
    system = 'win' if os.name == 'nt' else 'lin'
    name = "Kindleo_{}_{}".format(version, system)
    name = os.path.join("releases", name)
    if os.path.exists(name):
        print("Folder {} already exists".format(name))
        return

    compile_script(name)
    change_json(version)
    copytree("src", name)
    shutil.make_archive(name, "zip", name)

if __name__ == "__main__":
    main()
