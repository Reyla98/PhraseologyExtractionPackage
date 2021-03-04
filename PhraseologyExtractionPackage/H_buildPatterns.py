######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# Copyright (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2021  #
######################################################################

import os
import sys
import pickle
import copy
import luigi
import pathlib

from lib.Pattern import Pattern
from . import G_groupEmbeddedTags as groupEmbeddedTags

from pprint import pprint

class buildPatterns(luigi.Task):
    """
    1. Group n-grams according to their common lemmas (similar to the grouping
    by simple tag described above).

    2. Add wildcards at the beginning and/or end of each n-gram in the same
    group so that their common lemmas appear at the same position (e.g. "there
    is a" and "if there is" would become "* there is a" and "if there is *"

    3. If two n-grams are of the maximal size of n, if they have the same
    frequency, and if all their tokens are the same (except for the first and
    last one), it is highly probable that they were extracted from the same
    sentence(s). For that reason, they are merged together to form an n-gram of
    size n+1.

    e.g. n = 5:

    - "I saw him last Friday" : frequency: 2
    - "saw him last Friday evening": frequency: 2
    - => "I saw him last Friday evening": frequency: 2

    **It can happen that two n-grams are grouped even if they come from two
    different sentences**, but this is quite rare. On the other hand, this step
    helps to identify n-grams that are overlapping and were not filtered by
    removeEmbeddedNgrams because n-grams of size n+1 were not extracted. Thus,
    it improves a lot the quality of the results, even if there might be a few
    mistakes.

    4. Build phraseological patterns from the n-grams that were grouped
    together in steps 1 to 3. By phraseological pattern, I mean a sequence of
    elements (tokens, lemmas, specific tags, simplified tags or wildcards) that
    are occurring in the corpus. Each pattern is composed of at least --m
    lemmas.

    4.1. To build a pattern, the elements of the n-grams are compared one by
    one. If, in a given position, all the n-grams have the same token, the
    token will be used in the pattern. If the tokens are different, but the
    lemma is always the same, the lemma will be used. Same for the specific
    tags, then simplified tags. If even the simplified tags do not match, a
    wildcard is used.

    4.2 Once the pattern is made, the n-grams used to build it are separated
    into several groups based first on the lemma that follows the common
    lemmas, then on the lemma that preceeds the common lemmas. For each group,
    a sub-pattern is created.

    With the following n-grams:

    - that it is
    - that it was
    - That it is
    - that it is the best
    - that it is a bad
    - that it is the worst
    - said that it is a bad
    - said that it was

    At step 2, the n-grams will be alligned as follow:

    - * that it is * *
    - * that it was * *
    - * That it is * *
    - * that it is the best
    - * that it is a bad
    - * that it is the worst
    - said that it is a bad
    - said that it was * *
    - said that it is * *

    At step 4.1, the following pattern will be built:

    - (said) °that° it °be° (the/a) *

    (See next section for details about the display.)

    At step 4.2, the n-grams will be grouped in this way:

    group 1:

    - * that it is the best
    - * that is is the worst

    group 2:

    - * that it is a bad
    - said that it is a bad

    group 3:

    - said that it was * *
    - said that it is * *

    For each group, a sub-pattern will be created in the same ways as before.
    """

    config = luigi.DictParameter()

    def requires(self):
        return groupEmbeddedTags.groupEmbeddedTags(config=self.config)

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
