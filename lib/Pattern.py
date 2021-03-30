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
        self.nbr_var = None
        self.elems = None
        self.types = None
        self.freq = None    #list of int
        self.node = None    #index of 1st & last common tokens
        self.DP = None
        self.subPat = None  #list of Patterns
        self.deepness = deepness #number of parent patterns


        #### define some useful functions ####
        def matchNgrams(n1, n2):
            for e1, e2 in zip(n1, n2):
                if e1 == "*" or e1 == e2:
                    pass
                else:
                    return False
            return True


        def realign(ngram):
            if ngram.tokens[-1] == "*":
                ngram.removeSlotEnd()
                ngram.addSlotStart(1)
            else:
                raise ValueError


        def resetAlign(ngram_ref, ngram_cur):
            while ngram_cur.tokens[0] == "*":
                ngram_cur.removeSlotStart()
                ngram_cur.addSlotEnd(1)

            while len(ngram_cur) < len(ngram_ref):
                ngram_cur.addSlotEnd(1)

            while not matchNgrams(ngram_ref.lemmas, ngram_cur.lemmas):
                ngram_cur.addSlotStart(1)
                ngram_cur.removeSlotEnd()


        #### initialize Pattern ####
        if len(ngram_list) == 1:
            ngram_ref = ngram_list[0]
            self.var = []
            self.nbr_var = 1
            self.elems = ngram_ref.tokens
            self.types = ["tk" for i in range(len(ngram_ref))]
            self.freq = ngram_ref.freq
            self.node = [0, None]
            self.DP = self.computeDP(subcorpora_prop)
            self.subPat = []
            self.deepness = deepness
            return

        ngram_ref = ngram_list[0]
        #print()
        #print(ngram_ref)
        tags_ref = ngram_ref.tags
        sple_tags_ref = ngram_ref.sple_tags
        freq = ngram_ref.freq.copy()
        tokens_ref = ngram_ref.tokens.copy()
        lemmas_ref = ngram_ref.lemmas.copy()
        elems = tokens_ref.copy()
        var = [ngram_ref]
        types = [None for i in range(len(elems))]

        elems_backup = elems.copy()
        types_backup = types.copy()

        for ngram_cur in ngram_list[1:]:
            #print(ngram_cur)

            not_aligned = True
            error = 0
            while not_aligned:
                not_aligned = False
                tokens_cur = ngram_cur.tokens
                lemmas_cur = ngram_cur.lemmas
                tags_cur = ngram_cur.tags
                sple_tags_cur = ngram_cur.sple_tags
                for i in range(len(elems)):
                    try:
                        if tokens_ref[i] == tokens_cur[i]:
                            if tokens_cur[i] != "*" and types[i] is None:
                                types[i] = "tk"
                        else:
                            if tokens_ref[i] == "*":
                                if tokens_cur[i] != "*":
                                    types[i] = "*"
                            elif lemmas_cur[i] == lemmas_ref[i]:
                                if types[i] == "tk" \
                                or types[i] is None:
                                    types[i] = "lem"
                                    elems[i] = lemmas_cur[i]
                            elif tags_cur[i] == tags_ref[i]:
                                if types[i] == "tk" \
                                or types[i] == "lem" \
                                or types[i] is None:
                                    types[i] = "tag"
                                    elems[i] = tags_cur[i]
                            elif sple_tags_cur[i] == sple_tags_ref[i]:
                                if types[i] == "tk" \
                                or types[i] == "lem" \
                                or types[i] == "tag"\
                                or types[i] is None:
                                    types[i] = "sple"
                                    elems[i] = sple_tags_cur[i]
                            else:
                                if self.deepness >= 1 :
                                    types[i] = "*"
                                    elems[i] = "*"
                                else:
                                    try:
                                        realign(ngram_cur)
                                    except ValueError:
                                        resetAlign(ngram_ref, ngram_cur)
                                    elems = elems_backup.copy()
                                    types = types_backup.copy()
                                    not_aligned = True
                                    error += 1 #################
                                    print(error)
                                    print("ref",ngram_ref.longStr())
                                    print("cur", ngram_cur.longStr())
                                    break

                    except IndexError:
                        ngram_cur.addSlotStart(1)
                        elems = elems_backup.copy()
                        types = types_backup.copy()
                        not_aligned = True
                        break

                    types_backup = types.copy()
                    elems_backup = elems.copy()

            if not not_aligned:
                var.append(ngram_cur)
                types_backup = types.copy()
                elems_backup = elems.copy()


        #### removing extra slots ####
        start = 0
        for t in types:
            if t is None:
                start += 1
                for v in var:
                    v.removeSlotStart()
            else:
                break
        types.reverse()
        end = 0
        for t in types:
            if t is None:
                end += 1
                for v in var:
                    v.removeSlotEnd()
            else:
                break
        types.reverse()

        if end != 0:
            elems = list(islice(elems, start, len(types)-end))
            types = types[start:-end]
        else:
            types = types[start:]
            elems = list(islice(elems, start, None))


        #### finding node (index of 1st & last common tokens) ####
        node = None
        count_common = 0
        for i, t in enumerate(types):
            if t != "lem" and t != "tk":
                if node is not None:
                    break
                count_common = 0
            else:
                count_common += 1
                if count_common >= m:
                    node = [i - count_common + 1, i + 1]


        #### compute freq
        freq = [0 for i in range(len(var[0].freq))]
        var.sort(key=len)
        counted_ngrams = set()

        for var_cur in var:
            #loop over all ngrams already counted. If none match, frequency is added
            if all(ngram not in var_cur.fullStr() for ngram in counted_ngrams):
                freq = [i + j for i, j in zip(freq, var_cur.freq)]
                counted_ngrams.add(var_cur.fullStr())


        #### initiate the pattern ####
        self.freq = freq
        self.elems = elems
        self.types = types
        self.var = var
        self.nbr_var = len(var)
        self.node = node
        self.subPat = []
        self.DP = self.computeDP(subcorpora_prop)


        #### group variants based on what follows the node ####
        # group variants per tag if odd deepness
        # group variants per lemma if even deepness

        try:
            after_node = self.node[1]
        except :
            print(self.elems)
            for ngram in self.var:
                print(ngram)
            print()
            return

        if deepness%2 == 0:
            elem = "lemmas"
        else:
            elem = "sple_tags"

        try:
            if after_node is not None: #there is sth after the node
                elem_vars = {}
                other = []
                for var_cur in self.var:
                    elem_var_cur = getattr(var_cur, elem)[after_node]
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

        except IndexError: #nothing after node
            pass

        #### group variants based on what precedes the node ####
        before_node = self.node[0] -1
        if before_node < 0: #nothing before node
            return

        elem_vars = {}
        other = []
        for var_cur in self.var:
            if isinstance(var_cur, Pattern):
                other.append(var_cur)
            else:
                elem_var_cur = getattr(var_cur, elem)[before_node]
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
        string = ""
        for i in range(len(self.elems)):
            if self.types[i] == "lem":
                string += f"*{self.elems[i]}* "
            elif self.types[i] == "*":
                if i < self.node[0]:
                    string = ""
                elif self.node[1] is not None and i >= self.node[1]:
                    return string.strip()
            elif self.types[i] == "tag":
                string += f"{self.elems[i]} "
            elif self.types[i] == "sple":
                string += f"*{self.elems[i]}* "
            else:
                string += f"{self.elems[i]} "

        return string.strip()


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


    def printAllVar(self, config, rank, file):
        if self.deepness == 0:
            if self.totFreq() < config['Min_Freq_Patterns']:
                return rank
            if config['Max_Nbr_Variants'] is not None\
            and self.nbr_var > config['Max_Nbr_Variants']:
                return rank
            if config['Min_Nbr_Variants'] is not None\
            and self.nbr_var < config['Min_Nbr_Variants']:
                return rank

        # check all conditions for parent pattern NOT to be printed
        if ( config['Min_Nbr_Variants'] is not None
        and len(self.var) < config['Min_Nbr_Variants'] ) \
        or ( config['Max_Nbr_Variants'] is not None
        and len(self.var) > config['Max_Nbr_Variants'] ) \
        or ( config['Min_Range'] is not None
        and self.computeRange() < config['Min_Range'] ) \
        or ( config['Max_Range'] is not None
        and self.computeRange() > config['Max_Range'] ):
            return rank

        if config['positions'] is not None:
            for i in range(len(self.freq)):
                if i+1 in config['positions']:  #i+1 because index specified by user starts at 1 and not 0
                    if self.freq[i] == 0:
                        return rank
                else:
                    if self.freq[i] != 0 :
                        return rank


        # all conditions are fullfilled, parent pattern is printed
        if self.deepness > 0:
            file.write("\t" * self.deepness + self.longStr())
        else:
            rank += 1
            file.write(str(rank) + "  " + self.longStr())

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
                        file.write("\t" * (self.deepness+1) + var_cur.longStr())
                    else:
                        var_cur.printAllVar(config, rank, file)

        file.write("\n")
        return rank


    def __hash__(self):
        return hash(self.longStr())
