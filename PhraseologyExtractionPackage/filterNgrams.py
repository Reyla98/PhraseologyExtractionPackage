######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# copywrithe (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2020  #
######################################################################

import pickle
import luigi
import os
import re
import pathlib

from lib.Ngram import Ngram
from . import groupNgrams

class filterNgrams(luigi.Task):
    """
    Check all the stop words and must-include words lists and filter the
    n-grams accordingly. If the option -r is set, the stop words and
    must-include words are parsed as regular expressions. Otherwise, they are
    considered as simple strings.
    
    9 stop words lists can be set: three for words occurring at the first
    position of the n-gram ("beg"), three for words occurring at the last
    position ("end"), three for words occurring at any place in the n-grams;
    each time one for specifying respectively tokens, lemmas or tags.
    
    3 must-include words lists can be set: one for specifying tokens, one for
    lemmas, and one for tags. 
    
    For an n-gram to be kept, it must contain none of the stop words and all
    the must-include words.

    """

    config = luigi.DictParameter()
    i = luigi.IntParameter()


    def requires(self):
        return groupNgrams.groupNgrams(
                config=self.config,
                i=self.i)


    def output(self):
        return luigi.LocalTarget(pathlib.Path(
                "{}/filterNgrams/{}{}sw{}iw{}/{}".format(
                self.config['DB'],
                self.config['folder_name'],
                self.config['full_stop'],
                self.config['sw'],
                self.config['iw'],
                self.i
                )
        ), format=luigi.format.Nop)


    def run(self):
        def loadNgrams(fin):
            while True:
                try:
                    yield pickle.load(fin)
                except EOFError:
                    break

        input_file = pathlib.Path("{}/groupNgrams/{}{}.ngrams{}".format(
            self.config['DB'],
            self.config['folder_name'],
            self.config['full_stop'],
            self.i
            ))

        #make the output folder if does not already exist
        try:
            os.mkdir("{}/filterNgrams/{}{}sw{}iw{}".format(
                self.config['DB'],
                self.config['folder_name'],
                self.config['full_stop'],
                self.config['sw'],
                self.config['iw'],
                )
            )
        except FileExistsError:
            pass

        with open(input_file, "rb") as fin, self.output().open("wb") as fout:
            for ngram in loadNgrams(fin):
                if checkMustInclude(ngram, self.config) \
                and checkStopWordsNgram(ngram, self.config):
                    pickle.dump(ngram, fout)
       

def checkStopWordsNgram(ngram, config):
    for elem, ngram_attr in zip(["tk", "lem", "tag"],
                                ["tokens", "lemmas", "tags"]):

        for position in ["beg", "mid", "end"]:
            sw = "sw_{}_{}".format(position, elem)
            ngram_elem = getattr(ngram, ngram_attr)

            for stopword in config[sw]:
                if position == "mid":
                    if config['regex']:
                        for ngram_elem_cur in ngram_elem:
                            if re.fullmatch(stopword, ngram_elem_cur) is not None:
                                return False
                    else:
                        for ngram_elem_cur in ngram_elem:
                            if stopword in ngram_elem_cur:
                                return False
                elif position == "end":
                    if config['regex']:
                        if re.fullmatch(stopword, ngram_elem[-1]) is not None:
                            return False
                    else:
                        if stopword == ngram_elem[-1]:
                            return False
                else:
                    if config['regex']:
                        if re.fullmatch(stopword, ngram_elem[0]) is not None:
                            return False
                    else:
                        if stopword == ngram_elem[0]:
                            return false
    return True


def checkMustInclude(ngram, config):
    for elem, ngram_attr in zip(["lem", "tag", "tk"],
                                ["lemmas", "tags", "tokens"]):
        iw = "must_include_" + elem
        if config['regex']:
            for regex in config[iw]:
                matches = [re.fullmatch(regex, elem) for elem in getattr(ngram, ngram_attr)]
                if not any (match is not None for match in matches):
                    return False
        elif not all(word in getattr(ngram, ngram_attr) for word in config[iw]):
            return False

    return True


def main(config):
    luigi.build([createNgramBin(config=config)])
