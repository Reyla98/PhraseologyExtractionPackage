######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# copywrithe (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2020  #
######################################################################

import re
import os
import pickle
import sys
import luigi
import pathlib

from tempfile import gettempdir
from lib.Ngram import Ngram
from lib.Pattern import Pattern
from . import removeEmbeddedNgrams


class groupEmbTags(luigi.Task):

    config = luigi.DictParameter()


    def requires(self):
        return removeEmbeddedNgrams.removeEmbeddedNGrams(config=self.config)


    def output(self):
        return luigi.LocalTarget(
            pathlib.Path("{}/groupEmbTags/{}{}_sw{}iw{}-{}-{}".format(
                self.config['DB'],
                self.config['folder_name'],
                self.config['full_stop'],
                self.config['sw'],
                self.config['iw'],
                self.config['m'],
                self.config['n'],
                ))
        )


    def run(self):
        def loadNgrams(fin):
            while True:
                try:
                    yield pickle.load(fin)
                except EOFError:
                    break

        input_folder = pathlib.Path(
            "{}/removeEmbNgrams/{}{}_sw{}iw{}-{}-{}".format(
                self.config['DB'],
                self.config['folder_name'],
                self.config['full_stop'],
                self.config['sw'],
                self.config['iw'],
                self.config['m'],
                self.config['n'],
                )
            )

        input_files = os.listdir(input_folder)
        input_files.sort(key=int)

        output_folder = pathlib.Path(
            "{}/groupEmbTags/{}{}_sw{}iw{}-{}-{}".format(
                self.config['DB'],
                self.config['folder_name'],
                self.config['full_stop'],
                self.config['sw'],
                self.config['iw'],
                self.config['m'],
                self.config['n'],
                )
            )
        
        try:
            os.mkdir(output_folder)
        except FileExistsError:
            pass



        for file in input_files:
            with open(str(pathlib.Path(input_folder)) +
                      str(pathlib.Path(f"/{file}")), "rb") as fin:
                for ngram in loadNgrams(fin):
                    flag = False
                    sple_tags = " ".join(ngram.sple_tags)

                    for fout in os.listdir(output_folder):
                        if fout in sple_tags:
                            with open(str(pathlib.Path(output_folder)) +
                                      str(pathlib.Path(f"/{fout}")), "ab") \
                            as output:
                                pickle.dump(ngram, output)
                            flag = True
                    if not flag:
                        with open(str(pathlib.Path(output_folder)) +
                                  str(pathlib.Path(f"/{sple_tags}")), "wb") \
                        as output:
                            pickle.dump(ngram, output)


def main(config):
    luigi.build([groupEmbTags(config=config)])
