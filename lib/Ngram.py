######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# Copyright (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2021   #
######################################################################

import re

from collections import deque


class Ngram:
    def __init__(self, TTngram, sple_tag_corr):

        match = re.fullmatch("(.+)\t(([0-9]+ )*[0-9]+)\n", TTngram)

        if match is None:
            raise ValueError("Invalid file format.\n")

        self.freq = [int(i) for i in match.group(2).split(" ")]

        self.tokens = deque()
        self.tags = deque()
        self.lemmas = deque()
        self.sple_tags = deque()
        for TTline in match.group(1).split("||"):
            (token, tag, lemma) = TTline.split("\t")
            self.tokens.append(token)
            self.tags.append(tag)
            self.lemmas.append(lemma)
            if  sple_tag_corr is not None:
                try:
                    self.sple_tags.append(sple_tag_corr[tag])
                except KeyError:
                    self.sple_tags.append("OTH")

        self.string = " ".join(self.tokens)

        if sple_tag_corr is None:
            self.sple_tags = self.tags

        self.DP = 0


    def computeRange(self):
        disp_range = 0
        for freq_cur in self.freq:
            if freq_cur != 0:
                disp_range += 1
        return disp_range


    def computeDP(self, subcorpora_prop):
        #### no dispersion, only one subcorpus ####
        if len(subcorpora_prop) == 1:
            return 1

        #### determine the proportion of occurrences in each subcorpus ####
        total_occurrences = self.totFreq()
        occurrences_prop = []
        for nbr_occurrence_cur in self.freq:
            occurrences_prop.append(nbr_occurrence_cur / total_occurrences)

        #### determine the difference between expected and observed occ ####
        difference = [ abs(i - j) for i, j in zip(subcorpora_prop, occurrences_prop)]

        #### sum up and divide by 2 ####
        res =  sum(difference) / 2

        return res


    def addSlotEnd(self, nbr, val=None):
        if val is None:
            self.tokens.extend(["*"] * nbr)
            self.tags.extend(["*"] * nbr)
            self.lemmas.extend(["*"] * nbr)
            self.sple_tags.extend(["*"] * nbr)
        else:
            self.tokens.append(val[0])
            self.tags.append(val[1])
            self.lemmas.append(val[2])
            self.sple_tags.append(val[3])


    def removeSlotEnd(self):
        self.tokens.pop()
        self.tags.pop()
        self.lemmas.pop()
        self.sple_tags.pop()


    def addSlotStart(self, nbr):
        self.tokens.extendleft(["*"] * nbr)
        self.tags.extendleft(["*"] * nbr)
        self.lemmas.extendleft(["*"] * nbr)
        self.sple_tags.extendleft(["*"] * nbr)


    def removeSlotStart(self):
        self.tokens.popleft()
        self.tags.popleft()
        self.lemmas.popleft()
        self.sple_tags.popleft()


    def totFreq(self):
        return sum(self.freq)


    def getN(self):
        nbr_tokens = 0
        for elem in self.tokens:
            if elem != "*":
                nbr_tokens += 1
        return nbr_tokens


    def longStr(self):
        return "{}\t{}\t{:0.3f}\t{}\n".format(
            " ".join(self.tokens).strip(" *"),
            self.totFreq(),
            self.DP,
            self.freq
            )


    def fullStr(self):
        words = zip(self.tokens, self.lemmas, self.tags)
        full_str = "|"
        for word in words:
            if word[0] == "*":
                continue
            full_str += "".join(word)
            full_str += "|"

        return full_str


    def nbr_tokens(self):
        nbr_tokens = 0
        for token in self.tokens:
            if token != "*":
                nbr_tokens += 1
        return nbr_tokens


    def __len__(self):
        return len(self.tokens)


    def __str__(self):
        #return " ".join(self.tokens) + "\t" + str(self.freqCum())
        return self.string


    def __eq__(self, other):
        return self.freq == other.freq \
        and all( (tk1 == tk2 or tk1 == "*" or tk2 == "*")
            for tk1, tk2 in zip(self.tokens, other.tokens))


    def __hash__(self):
        return hash(self.fullStr())


    def __contains__(self, other):
        """ return True if other matches the beginning of self"""
        return all(tk1 == tk2 for tk1, tk2 in zip(self.tokens, other.tokens))


    def __lt__(self, other):
        return self.string < other.string

    def __gt__(self, other):
        return self.string > other.string

    def __le__(self, other):
        return self.string <= other.string

    def __ge__(self, other):
        return self.string >= other.string
