######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# copywrithe (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2020  #
######################################################################

import os
import pickle
import luigi
import itertools
import pathlib

from . import filterNgrams

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
            return a list of ngrams of size n if they are not embedded
            in ngram of size n+1 (compare only the beginning of the
            ngrams)
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


        def compareNgramLists(l1, l2, n):
            def sort_on_end(ngram):
                return ngram.string[::-1]
            ngram_list = sorted(itertools.chain(l1, l2),
                                key=sort_on_end)
            small_ngram_list_filtered = removeEmbNgrams(ngram_list, n)
            return small_ngram_list_filtered


        def compareNgrams(small_ngram_list, f2, n):
            """
            small_ngram_list is either a list or a generator
            f2 is a file
            """

            # filter from the start
            long_ngram_list = []
            small_ngram_list_filtered = []

            try:
                long_ngram = next(loadNgrams(f2))
                long_ngram_list.append(long_ngram)
            except StopIteration:
                if isinstance(small_ngram_list, list):
                    small_ngram_list_filtered = compareNgramLists(
                        small_ngram_list_filtered,
                        long_ngram_list, n)
                    return small_ngram_list, long_ngram_list
                else:
                    small_ngram_list_filtered = [ngram for ngram in small_ngram_list]
                    if small_ngram_list_filtered is None:
                        small_ngram_list_filtered = []
                    small_ngram_list_filtered = compareNgramLists(
                        small_ngram_list_filtered,
                        long_ngram_list, n)
                    return (small_ngram_list_filtered,
                    long_ngram_list)

            for i, small_ngram in enumerate(small_ngram_list):
                while long_ngram < small_ngram:
                    long_ngram_list.append(long_ngram)
                    try:
                        long_ngram = next(loadNgrams(f2))
                    except StopIteration:
                        if not isinstance(small_ngram_list, list):
                            for small_ngram in small_ngram_list:
                                small_ngram_list_filtered.append(small_ngram)
                        else:
                            small_ngram_list_filtered.extend(
                                small_ngram_list[i-1:])
                        small_ngram_list_filtered = compareNgramLists(
                            small_ngram_list_filtered,
                            long_ngram_list, n)
                        return small_ngram_list_filtered, long_ngram_list

                if (small_ngram.freq != long_ngram.freq
                or small_ngram.string not in long_ngram.string):
                    small_ngram_list_filtered.append(small_ngram)

            for long_ngram in loadNgrams(f2):
                long_ngram_list.append(long_ngram)


            # filter from the end
            small_ngram_list_filtered = compareNgramLists(
                small_ngram_list_filtered,
                long_ngram_list, n)

            return small_ngram_list_filtered, long_ngram_list


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
                    small_ngram_file = open(input_file1, "rb")
                    small_ngram_list = loadNgrams(small_ngram_file)
                else:
                    small_ngram_list = long_ngram_list

                long_ngram_file = open(input_file2, "rb")

                small_ngram_list_filtered, long_ngram_list = compareNgrams(small_ngram_list,
                                                              long_ngram_file,
                                                              i)

                try:
                    small_ngram_file.close()
                except :
                    pass
                long_ngram_file.close()


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
