######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# copywrithe (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2020  #
######################################################################

import pickle
import os
import json
import luigi
import pathlib

from lib.Ngram import Ngram
from . import Xngrams

class createNgramBin(luigi.Task):

    file = luigi.Parameter()
    config = luigi.DictParameter()
    i = luigi.IntParameter()


    def requires(self):
        return Xngrams.Xngrams(
                file=self.file,
                config=self.config,
                i=self.i)


    def output(self):
        corpus_name = os.path.splitext(os.path.basename(self.file))[0]
        return luigi.LocalTarget(
            pathlib.Path("{}/createNgramBin/{}{}.ngrams{}".format(
                self.config['DB'],
                corpus_name,
                self.config['full_stop'],
                self.i
                )
            )
        )


    def run(self):
        corpus_name = os.path.splitext(os.path.basename(self.file))[0]
        input_file = pathlib.Path("{}/Xngrams/{}{}.ngrams{}".format(
            self.config['DB'],
            corpus_name,
            self.config['full_stop'],
            self.i
            ))

        output_file = pathlib.Path("{}/createNgramBin/{}{}.ngrams{}".format(
            self.config['DB'],
            corpus_name,
            self.config['full_stop'],
            self.i
            ))


        # build a dict with correlations b/ specific tags and sple tags
        with open(self.config['sple_tagset']) as sple_tags_file:
            sple_tagset = json.load(sple_tags_file)




        # build instances of Ngrams and dumps them into a file
        with open(input_file) as fin, \
        open(output_file, "wb") as fout:

            line = fin.readline().strip() #1st line contains subcorpus size
            pickle.dump(int(line), fout)

            for line in fin.readlines():
                ngram = Ngram(line, sple_tagset)
                pickle.dump(ngram, fout)


def main(config):
    luigi.build([createNgramBin(config=config)])
