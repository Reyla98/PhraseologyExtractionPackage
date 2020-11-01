######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# copywrithe (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2020  #
######################################################################

import os
import re
import sys
import pickle
import luigi
import pathlib

from . import createNgramBin


class groupNgrams(luigi.Task):

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
            ))
        )


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
            )) for corpus_name in self.config['corpus_name']]


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
        file_cur = 0
        for file in input_files:
            with open(file, "rb") as fin:
                file_cur += 1
                next(loadNgrams(fin)) #we skip the 1st line (subcorpus size)
                for ngram in loadNgrams(fin):
                    freq = ngram.freq[0]
                    ngram_disp.setdefault(ngram,
                                        [0 for i in range(file_cur - 1)])
                    ngram_disp[ngram].append(freq)

            #if some ngrams were not present in the current file,
            #  we add them "0" frequency
            for ngram, freq in ngram_disp.items():
                if len(freq) < file_cur:
                    ngram_disp[ngram].append(0)


        #now that we have all the frequencies stored in the dict ngram_disp,
        #  we update them in the Ngram objects, and compute DP
        for ngram, freq in ngram_disp.items():
            ngram.freq = freq
            ngram.DP = ngram.computeDP(subcorpora_prop)


        with open(pathlib.Path("{}/groupNgrams/{}{}.ngrams{}".format(
            self.config['DB'],
            self.config['folder_name'],
            self.config['full_stop'],
            self.i
            )), "wb") as fout:
            for ngram in sorted(ngram_disp.keys()):
                pickle.dump(ngram, fout)


def main(config):
    for i in range(config['m'], config['n']+1):
        luigi.build([groupNgrams(i=i, config=config)])
