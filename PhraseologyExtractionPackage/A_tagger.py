######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# Copyright (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2021  #
######################################################################

import re
import os
import sys
import subprocess
import luigi
import pickle
import pathlib

from collections import ChainMap



class Tagger(luigi.Task):
    """
    Launch tree-tagger, as a subprocess, on the corpus, with the tree-tagger
    command specified by the --tree-tagger argument. The default options of
    tree-tagger are used. words between <> are ignored by tree-tagger, so
    they will be ignored by PEP too. If you want to keep them, remove the <>
    symbols.
    """

    file = luigi.Parameter()
    config = luigi.DictParameter()

    def requires(self):
        return []

    def output(self):
        corpus_name = os.path.splitext(os.path.basename(self.file))[0]
        return luigi.LocalTarget(
            pathlib.Path("{}/tagger/{}{}".format(
                self.config['DB'],
                corpus_name,
                self.config['full_stop'])))

    def run(self):
        corpus_name = os.path.splitext(os.path.basename(self.file))[0]
        tmp_file = str(pathlib.Path(self.config['tmp'])) + \
                   str(pathlib.Path(f"/{corpus_name}.TT"))
        if sys.platform == "win32" or sys.platform == "cygwin":
            TT_command = f"tag-{self.config['language']}"
        else:
            TT_command = f"tree-tagger-{self.config['language']}"

        sent_list = []
        token_list = []

        nbr_err = 0
        nbr_words = 0

        try:
            os.mkdir(self.config['tmp'])
        except FileExistsError:
            pass

        with open(tmp_file, "w", encoding="utf-8") as TTfile:
            tree_tagger = subprocess.run(
                f"{TT_command} {self.file}",
                stdout = TTfile,
                stderr = subprocess.DEVNULL,
                shell=True)
        with open (tmp_file, "r", encoding="utf-8") as TTfile:
            for TTline in TTfile.readlines():
                TTline = TTline.strip()
                match = re.fullmatch(f".+\t(.+)\t.+", TTline)
                if match is not None: # match is None if invalid TT line
                    nbr_words += 1
                    token_list.append(TTline)
                    if match.group(1) == self.config['full_stop']:
                        sent_list.append(token_list)
                        token_list = []
            sent_list.append(token_list)

        os.remove(tmp_file)


        with open(pathlib.Path("{}/tagger/{}{}".format(
                self.config['DB'],
                corpus_name,
                self.config['full_stop'])), "wb") as fout:
            pickle.dump(nbr_words, fout)
            pickle.dump(sent_list, fout)


def main(config):
    for file in config['corpora']:
        luigi.build([Tagger(file=file,
                            config=config
                            )])
