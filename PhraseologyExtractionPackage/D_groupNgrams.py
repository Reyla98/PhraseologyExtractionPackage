######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# Copyright (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2021  #
######################################################################

import os
import re
import sys
import pickle
import luigi
import pathlib

from . import C_createNgramBin as createNgramBin


class groupNgrams(luigi.Task):
    """
    Group n-grams of the same size across all the sub-corpora, if several were
    provided. The frequency of each n-gram is updated to be a list of the
    number of occurrences in each sub-corpus.
    """

    config = luigi.DictParameter()
    i = luigi.IntParameter()


    def requires(self):
        requirements = []
        for file in self.config['corpora']:
            requirements.append(createNgramBin.createNgramBin(
                file=file,
                config=self.config,
                i=self.i))
        return requirements


    def output(self):
        return luigi.LocalTarget(
            pathlib.Path("{}/groupNgrams/{}{}.ngrams{}".format(
                self.config['DB'],
                self.config['folder_name'],
                self.config['full_stop'],
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


        input_files = [pathlib.Path("{}/createNgramBin/{}{}.ngrams{}".format(
            self.config['DB'],
            corpus_name,
            self.config['full_stop'],
            self.i
            )) for corpus_name in self.config['corpora_names']]


        #compute the proportional size of each subcorpur
        #  (the 1st line of each file is the number of words in the sub-corpus)
        subcorpora_size = []
        for file in input_files:
            with open(file, "rb") as fin:
                subcorpora_size.append(pickle.load(fin))

        total_size = sum(subcorpora_size)
        subcorpora_prop = [size / total_size for size in subcorpora_size]

        with open(pathlib.Path("{}/subcorporaProp/{}".format(
            self.config['DB'],
            self.config['folder_name']
        )), "wb") as fout:
            pickle.dump(subcorpora_prop, fout)


        #put the ngrams in a dict with their freq in each subcorpus
        ngram_disp = {}
        for file_cur, file in enumerate(input_files):
            with open(file, "rb") as fin:
                next(loadNgrams(fin)) #we skip the 1st line (subcorpus size)
                for ngram in loadNgrams(fin):
                    freq_cur = ngram.freq[0]
                    if ngram not in ngram_disp:
                        ngram.freq = [0 for i in range(file_cur)]
                        ngram_disp[ngram] = ngram
                    ngram_disp[ngram].freq.append(freq_cur)

            #if some ngrams were not present in the current file,
            #  we add them "0" frequency
            for ngram in ngram_disp.values():
                if len(ngram.freq) < file_cur + 1:
                    ngram.freq.append(0)

        #now that we have all the frequencies stored in the dict ngram_disp,
        #  we compute DP and store the ngrams into a file
        with self.output().open("wb") as fout:
            for ngram in sorted(ngram_disp.values()):
                ngram.DP = ngram.computeDP(subcorpora_prop)
                pickle.dump(ngram, fout)


def main(config):
    for i in range(config['m'], config['n']+1):
        luigi.build([groupNgrams(i=i, config=config)])
