
######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# copywrithe (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2020  #
######################################################################

import re
import os
import sys
import pathlib
import subprocess
import luigi
import pickle

from collections import ChainMap
from tempfile import gettempdir
from . import A_tagger as tagger

class Xngrams(luigi.Task):
    """
    Extract n-grams (sequences of n words) in each sub-corpus, for each size of
    n specified, i.e. all integers between the -m and -n parameters included.
    If the --full_stop [TAG] parameter is specified, no n-gram overlapping two
    sentences will be extracted. [TAG] must be the tag used by tree-tagger for
    end of sentences.

    It is highly recommended to use this option if the corpus is large, since
    it will reduce the number of n-gram extracted from the beginning of the
    pipeline.
    """

    file = luigi.Parameter()
    config = luigi.DictParameter()
    i = luigi.IntParameter()


    def requires(self):
        corpus_name = os.path.splitext(os.path.basename(self.file))[0]
        return [tagger.Tagger(file=self.file,
                        config=self.config
                        )]


    def output(self):
        corpus_name = os.path.splitext(os.path.basename(self.file))[0]
        return luigi.LocalTarget(pathlib.Path("{}/Xngrams/{}{}.ngrams{}".format(
            self.config['DB'],
            corpus_name,
            self.config['full_stop'],
            self.i
            )
        ), format=luigi.format.UTF8)


    def run(self):

        # loads the output of PEP.tagger
        corpus_name = os.path.splitext(os.path.basename(self.file))[0]
        with open(pathlib.Path("{}/tagger/{}{}".format(
                self.config['DB'],
                corpus_name,
                self.config['full_stop'])), "rb") as fin:
            nbr_words = pickle.load(fin)
            sentences = pickle.load(fin)

        # build the ngrams
        ngram_freq = {}
        for tokens in sentences:
            for j in range(len(tokens) - self.i + 1):
                ngram = tokens[j:j + self.i]
                ngram = "||".join([e for e in ngram])
                ngram_freq.setdefault(ngram, 0)
                ngram_freq[ngram] += 1

        # write the output
        with self.output().open("w") as fout:
            fout.writelines(f"{nbr_words}\n")
            for ngram, freq in ngram_freq.items():
                fout.writelines(f"{ngram}\t{freq}\n")


def main(config):
    for file in config['corpora']:
        for i in range(config['m'], config['n']+1):
            luigi.build([Xngrams(file=file,
                                i=i,
                                config=config
                                )])
