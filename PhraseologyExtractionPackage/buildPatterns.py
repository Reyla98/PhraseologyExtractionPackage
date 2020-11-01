######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# copywrithe (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2020  #
######################################################################

import os
import sys
import pickle
import copy
import luigi
import pathlib

from lib.Pattern import Pattern
from . import groupEmbTags

from pprint import pprint

class buildPatterns(luigi.Task):

    config = luigi.DictParameter()

    def requires(self):
        return groupEmbTags.groupEmbTags(config=self.config)

    def output(self):
        return luigi.LocalTarget(pathlib.Path(
            "{}/buildPatterns/{}{}_sw{}iw{}-{}-{}".format(
                self.config['DB'],
                self.config['folder_name'],
                self.config['full_stop'],
                self.config['sw'],
                self.config['iw'],
                self.config['m'],
                self.config['n'],
                )
            )
        )


    def run(self):
     
        def groupIdentical(lemmas_gram):
            def groupNgrams(ngram1, ngram2):
                """
                Merge the tokens of ngram1 and ngram2
                ngram1 and ngram2 are supposed to be equal
                """

                for i, (tk1, tk2) in enumerate(zip(ngram1.tokens, ngram2.tokens)):
                    if tk1 == tk2:
                        continue
                    if tk1 == "*":
                        ngram1.tokens[i] = ngram2.tokens[i]
                        ngram1.lemmas[i] = ngram2.lemmas[i]
                        ngram1.tags[i] = ngram2.tags[i]
                        ngram1.sple_tags[i] = ngram2.sple_tags[i]

                return ngram1


            for ngram_list in lemmas_gram.values():
                changed = True
                while changed:
                    changed = False
                    try:
                        for i in range(len(ngram_list)):
                            i_tokens = list(filter(lambda a: a != "*", ngram_list[i].tokens))

                            if len(i_tokens) < self.config['n']:
                                continue

                            for j in range(i+1, len(ngram_list)):
                                j_tokens = list(filter(lambda a: a != "*", ngram_list[j].tokens))

                                if len(j_tokens) < self.config['n']:
                                    continue

                                if ngram_list[i] == ngram_list[j]:
                                    ngram_list[i] = groupNgrams(ngram_list[i], ngram_list[j])
                                    ngram_list.pop(j)
                                    changed = True
                                else:
                                    pass

                    except IndexError:
                        pass


        def matchNgrams(n1, n2):
            for e1, e2 in zip(n1, n2):
                if e1 == "*" or e1 == e2:
                    pass
                else:
                    return False
            return True


        def alignNgrams(lemmas_gram):
            for ngram_list in lemmas_gram.values():
                if len(ngram_list) == 1:
                    continue

                max_size = max([len(ngram) for ngram in ngram_list])

                ngram_ref = ngram_list[0]
                ngram_ref.addSlotStart(max_size - self.config['m'])

                size = len(ngram_ref)

                #### align start ####
                for ngram_cur in ngram_list[1:]:
                    flag = True
                    while flag:
                        ngram_cur.addSlotStart(size - len(ngram_cur))
                        if matchNgrams(ngram_ref.lemmas, ngram_cur.lemmas):
                            ngram_cur.addSlotEnd(size - len(ngram_cur))
                            flag = False
                        else:
                            ngram_cur.addSlotStart(1)

                #### align end ####
                ngram_list[0].addSlotEnd(max_size - self.config['m'])
                size = len(ngram_list[0])
                for ngram in ngram_list[1:]:
                    ngram.addSlotEnd(size - len(ngram))

            return lemmas_gram


        def sortNgramsPerLemma(ngram_list):
            lemmas_gram = {}
            for ngram in ngram_list:
                flag = True
                key_cur = " " + " ".join(ngram.lemmas) + " "
                for key in lemmas_gram.keys():
                    if key in key_cur:
                        lemmas_gram[key].append(copy.deepcopy(ngram))
                        flag = False
                if flag:
                    lemmas_gram[key_cur] = [ngram]

            return lemmas_gram


        def lemmaGrams2Pattern(lemmas_gram, subcorpora_prop):
            patterns = []

            for ngram_list in lemmas_gram.values():
                pattern = Pattern(ngram_list, self.config['m'], subcorpora_prop)
                patterns.append(pattern)

            return patterns


        def main():
            input_folder = pathlib.Path(
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

            output_folder = pathlib.Path(
                "{}/buildPatterns/{}{}_sw{}iw{}-{}-{}".format(
                    self.config['DB'],
                    self.config['folder_name'],
                    self.config['full_stop'],
                    self.config['sw'],
                    self.config['iw'],
                    self.config['m'],
                    self.config['n'],
                    )
                )
                
            os.mkdir(output_folder)

            already_a_pattern = set() #keeps track of all created patterns to
                                      #  avoid duplicates

            with open(str(pathlib.Path(self.config['DB'])) +
                      str(pathlib.Path(f"/subcorporaProp/{self.config['folder_name']}")),
                "rb") as fin:
                subcorpora_prop = pickle.load(fin)

            identifier = 1

            for input_file in os.listdir(input_folder):
                with open(pathlib.Path(input_folder).joinpath(input_file), "rb") as fin:
                    ngram_list = []
                    while True:
                        try:
                            ngram_list.append(pickle.load(fin))
                        except EOFError:
                            break

                lemmas_gram = sortNgramsPerLemma(ngram_list)
                alignNgrams(lemmas_gram)         
                groupIdentical(lemmas_gram)
                patterns = lemmaGrams2Pattern(lemmas_gram, subcorpora_prop)

                for pattern in patterns:
                    try:
                        if hash(pattern) not in already_a_pattern:
                            with open(str(pathlib.Path(output_folder)) +
                                      str(pathlib.Path("/{}_{}_{}".format(
                                            identifier,
                                            pattern.totFreq(),
                                            pattern.DP))), "wb") \
                            as fout:
                                pickle.dump(pattern, fout)
                            identifier += 1
                            already_a_pattern.add(hash(pattern))
                    except TypeError:
                        continue

        main()


def main(config):
    luigi.build([buildPatterns(config=config)])
