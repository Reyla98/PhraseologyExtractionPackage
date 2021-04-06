######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# Copyright (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2021   #
######################################################################

import sys

from itertools import islice
from lib.Ngram import Ngram

from pprint import pprint


class Pattern:

    def __init__(self, ngram_list, m, subcorpora_prop, deepness=0):
        #### set the attributes ####
        self.var = None     #list of Ngrams
        self.elems = None
        self.types = None
        self.freq = None    #list of int
        self.core = None    #index of 1st & last common tokens
        self.DP = None
        self.subPat = None  #list of Patterns
        self.deepness = deepness #number of parent patterns


        #### initialize Pattern if only 1 ngram ####
        if len(ngram_list) == 1:
            ngram_ref = ngram_list[0]
            self.var = []
            self.elems = ngram_ref.tokens
            self.types = ["tk" for i in range(len(ngram_ref))]
            self.freq = ngram_ref.freq
            self.core = [0, None]
            self.DP = self.computeDP(subcorpora_prop)
            self.subPat = []
            self.deepness = deepness
            return

        #### initialize Pattern if more than 1 ngram ####
        ngram_ref = ngram_list[0]
        tags_ref = ngram_ref.tags
        sple_tags_ref = ngram_ref.sple_tags
        tokens_ref = ngram_ref.tokens.copy()
        lemmas_ref = ngram_ref.lemmas.copy()
        elems = tokens_ref.copy()
        var = [ngram_ref]
        types = ["*" if x == "*" else "tk" for x in elems]

        for ngram_cur in ngram_list[1:]:
            aligned = False
            while not aligned:
                aligned = True
                tokens_cur = ngram_cur.tokens
                lemmas_cur = ngram_cur.lemmas
                tags_cur = ngram_cur.tags
                sple_tags_cur = ngram_cur.sple_tags
                for i in range(len(elems)):
                    try:
                        if tokens_cur[i] == "*":
                            pass
                        elif tokens_cur[i] == tokens_ref[i]:
                            pass
                        elif lemmas_cur[i] == lemmas_ref[i]:
                            if types[i] == "tk" \
                            or types[i] == "*":
                                types[i] = "lem"
                                elems[i] = lemmas_cur[i]
                        elif tags_cur[i] == tags_ref[i]:
                            if types[i] == "tk" \
                            or types[i] == "lem" \
                            or types[i] == "*" :
                                types[i] = "tag"
                                elems[i] = tags_cur[i]
                        elif sple_tags_cur[i] == sple_tags_ref[i]:
                            if types[i] == "tk" \
                            or types[i] == "lem" \
                            or types[i] == "tag" \
                            or types[i] == "*":
                                types[i] = "sple"
                                elems[i] = sple_tags_cur[i]
                        else:
                            types[i] = "*"
                            elems[i] = "*"

                    except IndexError:
                        ngram_cur.addSlotStart(1)
                        aligned = False
                        break

            var.append(ngram_cur)


        #### finding core (index of 1st & last common tokens) ####
        core = None
        count_common = 0
        for i, t in enumerate(types):
            if t != "lem" and t != "tk":
                if core is not None:
                    break
                count_common = 0
            else:
                count_common += 1
                if count_common >= m:
                    core = (i - count_common + 1, i + 1)


        #### compute freq
        freq = [0 for i in range(len(var[0].freq))]
        var.sort(key=len)
        counted_ngrams = set()

        for var_cur in var:
            #loop over all ngrams already counted. If none match, frequency is added
            if all(ngram not in var_cur.fullStr() for ngram in counted_ngrams):
                freq = [i + j for i, j in zip(freq, var_cur.freq)]
                counted_ngrams.add(var_cur.fullStr())


        #### set the right values for the attributes ####
        self.freq = freq
        self.elems = elems
        self.types = types
        self.var = var
        self.core = core
        self.subPat = []
        self.DP = self.computeDP(subcorpora_prop)


        #### group variants based on what follows the core ####
        # group variants per tag if odd deepness
        # group variants per lemma if even deepness

        try:
            after_core = self.core[1]
        except :
            print(self.elems)
            print(self.types)
            for ngram in self.var:
                print(ngram)
            print()
            return

        if deepness%2 == 0:
            elem = "lemmas"
        else:
            elem = "sple_tags"

        try:
            if after_core is not None: #there is sth after the core
                elem_vars = {}
                other = []
                for var_cur in self.var:
                    elem_var_cur = getattr(var_cur, elem)[after_core]
                    if elem_var_cur != "*":
                        elem_vars.setdefault(elem_var_cur, [])
                        elem_vars[elem_var_cur].append(var_cur)
                    else:
                        other.append(var_cur)

                self.var = []
                for ngram_list in elem_vars.values():
                    if len(ngram_list) == 1:
                        self.var.append(ngram_list[0])
                    else:
                        self.subPat.append(Pattern(ngram_list,
                                                   m,
                                                   subcorpora_prop,
                                                   deepness=deepness+1))

                for var_cur in other:
                   self.var.append(var_cur)

        except IndexError: #nothing after core
            pass

        #### group variants based on what precedes the core ####
        before_core = self.core[0] -1
        if before_core < 0: #nothing before core
            return

        elem_vars = {}
        other = []
        for var_cur in self.var:
            if isinstance(var_cur, Pattern):
                other.append(var_cur)
            else:
                elem_var_cur = getattr(var_cur, elem)[before_core]
                if elem_var_cur != "*":
                    elem_vars.setdefault(elem_var_cur, [])
                    elem_vars[elem_var_cur].append(var_cur)
                else:
                    other.append(var_cur)

        self.var = []
        for ngram_list in elem_vars.values():
            if len(ngram_list) == 1:
                self.var.extend(ngram_list)
            else:
                self.subPat.append(Pattern(ngram_list,
                                           m,
                                           subcorpora_prop,
                                           deepness=deepness+1))
        self.var.extend(other)

        #if only one pattern as variant, it is discarded and
        #its children are brought one level up
        if len(self.var) == 0 and len(self.subPat) == 1:
            self.var = self.subPat[0].var
            self.subPat = self.subPat[0].subPat


    def __eq__(self, other):
        if isinstance(other, Ngram):
            return all( (t == "tk" or e2 == "*" ) for e2, t in zip(other.tokens, self.types))
        else:
            return all( ( e1 == e2 or isinstance(e1, list) ) for e1, e2 in zip(self.elems, other.elems))


    def __len__(self):
        """
        return the len of self.elem disregarding the initial and final "*"
        """
        first_elem_index = 0
        last_elem_index = 0
        for i, e in enumerate(self.elems):
            if e != "*":
                if first_elem_index == 0:
                    first_elem_index == i
                last_elem_index = i
        return last_elem_index - first_elem_index + 1


    def totFreq(self):
        return sum(self.freq)


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


    def __str__(self):
        string = []
        for i in range(len(self.elems)):
            if self.types[i] == "tk":
                string.append(self.elems[i])
            elif self.types[i] == "lem":
                string.append(f"*{self.elems[i]}*")
            elif self.types[i] == "tag":
                string.append(self.elems[i])
            elif self.types[i] == "sple":
                string.append(f"*{self.elems[i]}*")
            elif self.types[i] == "*":
                if i < self.core[0]:
                    string = []
                elif self.core[1] is not None and i >= self.core[1]:
                    return " ".join(string)

        return " ".join(string)


    def longStr(self):
        return "{}\t{}\t{}\t{}\n".format(
            str(self),
            self.totFreq(),
            self.DP,
            self.freq
            )


    def getDP(self):
        return self.DP


    def computeRange(self):
        disp_range = 0
        for freq_cur in self.freq:
            if freq_cur != 0:
                disp_range += 1
        return disp_range


    def printAllVar(self, config, rank, stats, file):
        if self.deepness == 0 and self.totFreq() < config['Min_Freq_Patterns']:
            return rank, stats

        # check all conditions for parent pattern NOT to be printed
        if ( config['Min_Nbr_Variants'] is not None
        and len(self.var) < config['Min_Nbr_Variants'] ) \
        or ( config['Max_Nbr_Variants'] is not None
        and len(self.var) > config['Max_Nbr_Variants'] ) \
        or ( config['Min_Range'] is not None
        and self.computeRange() < config['Min_Range'] ) \
        or ( config['Max_Range'] is not None
        and self.computeRange() > config['Max_Range'] ):
            return rank, stats

        if config['positions'] is not None:
            for i in range(len(self.freq)):
                if i+1 in config['positions']:  #i+1 because index specified by user starts at 1 and not 0
                    if self.freq[i] == 0:
                        return rank, stats
                else:
                    if self.freq[i] != 0 :
                        return rank, stats


        # all conditions are fullfilled, parent pattern is printed
        if self.deepness > 0:
            file.write("\t" * self.deepness + self.longStr())
        else:
            rank += 1
            file.write(str(rank) + "  " + self.longStr())

        # freq of self added to stats
        if len(self.subPat) == 0 and len(self.var) <= 1:
            stats[0][len(self)][self.deepness+1] += 1
            stats[1][len(self)][self.deepness+1] += self.totFreq()
        else:
            stats[2][len(self)][self.deepness+1] += 1
            stats[3][len(self)][self.deepness+1] += self.totFreq()

        # we also print all its children according to the user parameters
        all_vars = self.var + self.subPat
        if config['Sort'] == "frequency":
            all_vars.sort(key=Pattern.totFreq, reverse=True)
        elif config['Sort'] == "dispersion":
            all_vars.sort(key=Pattern.getDP)

        for var_cur in all_vars:
            if self == var_cur:
                continue
            if var_cur.totFreq() >= config['Min_Freq_Examples']:
                if var_cur.totFreq() >= config['Proportion_Freq_Examples'] * self.totFreq():
                    if isinstance(var_cur, Ngram):
                        if ( config['Min_Range'] is not None
                        and var_cur.computeRange() < config['Min_Range'] ) \
                        or ( config['Max_Range'] is not None
                        and var_cur.computeRange() > config['Max_Range'] ) \
                        or (var_cur.DP > config['DP']):
                            continue
                        else:
                            file.write("\t" * (self.deepness+1) + var_cur.longStr())
                            stats[0][var_cur.nbr_tokens()][self.deepness+2] += 1
                            stats[1][var_cur.nbr_tokens()][self.deepness+2] += var_cur.totFreq()
                    else:
                        var_cur.printAllVar(config, rank, stats, file)

        file.write("\n")
        return rank, stats


    def __hash__(self):
        return hash(self.longStr())
