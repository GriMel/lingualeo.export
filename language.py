# !/usr/bin/env python
import argparse
import os


def createTs(language):
    src_file = "gui_export.py"
    lang_file = "qt_{}.ts".format(language)
    command = "pylupdate4 -verbose -noobsolete "\
              "{0} -ts {1}".format(src_file, lang_file)
    os.system(command)
    print("{} created".format(lang_file))


def createQm(language):
    ts_file = "qt_{}.ts".format(language)
    qm_file = "src/lang/qt_{}.qm".format(language)
    command = "lrelease-qt4 -verbose {0} "\
              "-qm {1}".format(ts_file, qm_file)
    os.system(command)
    print("{} created".format(qm_file))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind")
    parser.add_argument("language")
    args = parser.parse_args()

    kind = args.kind
    language = args.language
    if kind == 'ts':
        createTs(language)
    elif kind == 'qm':
        createQm(language)
    else:
        print("Wrong kind. Aborted")

if __name__ == "__main__":
    main()