######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# Copyright (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2021  #
######################################################################

import os
import pickle
import luigi
import itertools
import pathlib

from . import E_filterNgrams as filterNgrams

class removeEmbeddedNGrams(luigi.Task):
    """
    Remove those that are embedded in longer n-grams. An n-gram is embedded in
    a longer one if the longer one has all the tokens of the smaller one,
    appearing in the same order, and if they have exactly the same frequency in
    all sub-corpora.
    """

    config = luigi.DictParameter()


    def requires(self):
        requirements = []
        for i in range(self.config['m'], self.config['n'] + 1):
            requirements.append(filterNgrams.filterNgrams(config=self.config,
                                                          i=i))
        return requirements


    def output(self):
        return luigi.LocalTarget(
            pathlib.Path("{}/removeEmbNgrams/{}{}_sw{}iw{}-{}-{}".format(
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


        def removeEmbNgrams(ngram_list, n):
            """
            ngram_list is a list containing ngrams of size n and
            n + 1, sorted in alphabetical order
            return a list of ngrams of size n that are not embedded
            in ngrams of size n+1
            """
            if ngram_list == []:
                return []
            ngram_filtered = []
            for i, ngram in enumerate(ngram_list[:-1]):
                next_ngram = ngram_list[i+1]
                if ( ngram.freq != next_ngram.freq \
                or ngram.string not in next_ngram.string ) \
                and len(ngram) == n:
                    ngram_filtered.append(ngram)
            if len(ngram_list[-1]) == n:
                ngram_filtered.append(ngram_list[-1])
            return ngram_filtered


        def compareNgrams(small_ngram_list, long_ngram_list, n):
            def sortFromEnd(ngram):
                return ngram.string[::-1]

            # filter from start
            ngram_list = sorted(itertools.chain(small_ngram_list, long_ngram_list))
            small_ngram_list_filtered = removeEmbNgrams(ngram_list, n)

            # filter from the end
            ngram_list = sorted(itertools.chain(small_ngram_list_filtered, long_ngram_list), key=sortFromEnd)
            small_ngram_list_filtered = removeEmbNgrams(ngram_list, n)

            return small_ngram_list_filtered


        def main():
            input_folder = pathlib.Path("{}/filterNgrams/{}{}sw{}iw{}".format(
                    self.config['DB'],
                    self.config['folder_name'],
                    self.config['full_stop'],
                    self.config['sw'],
                    self.config['iw']
                    ))

            output_folder = pathlib.Path(
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

            try:
                os.mkdir(output_folder)
            except FileExistsError:
                pass


            small_ngram_list = []
            for i in range(self.config['m'], self.config['n']):
                input_file1 = str(input_folder) + f"/{i}"
                input_file2 = str(input_folder) + f"/{i+1}"

                if small_ngram_list == []:
                    with open(input_file1, "rb") as small_ngram_file:
                        small_ngram_list = [ngram for ngram in loadNgrams(small_ngram_file)]
                else:
                    small_ngram_list = long_ngram_list

                with open(input_file2, "rb") as long_ngram_file:
                    long_ngram_list = [ngram for ngram in loadNgrams(long_ngram_file)]

                small_ngram_list_filtered = compareNgrams(small_ngram_list,
                                                          long_ngram_list,
                                                          i)

                with open(str(output_folder) +
                          str(pathlib.Path(f"/{i}")), "wb")\
                as fout:
                    for ngram in small_ngram_list_filtered:
                        pickle.dump(ngram, fout)

            with open(str(output_folder) +
                      str(pathlib.Path(f"/{self.config['n']}")), "wb") \
            as fout:
                for ngram in long_ngram_list:
                    pickle.dump(ngram, fout)

        main()


def main(config):
    luigi.build([removeEmbeddedNGrams(config=config)])
