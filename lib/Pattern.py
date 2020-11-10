######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# copywrithe (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2020  #
######################################################################

import sys

from itertools import islice
from lib.Ngram import Ngram

from pprint import pprint

            
class Pattern:

    def __init__(self, ngram_list, m, subcorpora_prop, child=False):
        #### set the attributes ####
        self.var = None     #list of Ngrams
        self.nbr_var = None 
        self.elems = None
        self.types = None
        self.freq = None    #list of int
        self.node = None    #index of 1st & last common tokens
        self.DP = None
        self.subPat = None  #list of Patterns


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
            return

        ngram_ref = ngram_list[0]
        tags_ref = ngram_ref.tags
        sple_tags_ref = ngram_ref.sple_tags
        freq = ngram_ref.freq.copy()
        tokens_ref = ngram_ref.tokens.copy()
        lemmas_ref = ngram_ref.lemmas.copy()
        elems = tokens_ref.copy()
        var = [ngram_ref]
        types = [None for i in range(len(elems))]
        diff = [ {} for i in range(len(elems))]

        elems_backup = elems.copy()
        types_backup = types.copy()
    
        for ngram_cur in ngram_list[1:]:

            not_aligned = True
            #error = 0
            while not_aligned:
                not_aligned = False
                tokens_cur = ngram_cur.tokens
                lemmas_cur = ngram_cur.lemmas
                tags_cur = ngram_cur.tags
                sple_tags_cur = ngram_cur.sple_tags
                for i in range(len(elems)):
                    try:
                        if tokens_ref[i] != tokens_cur[i]:
                            if tokens_ref[i] == "*":
                                if tokens_cur[i] != "*":
                                    types[i] = "*"
                                if lemmas_cur[i] != "*":
                                    diff[i].setdefault(lemmas_cur[i], 0)
                                    diff[i][lemmas_cur[i]] += ngram_cur.totFreq()
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
                            elif sple_tags_cur == sple_tags_ref:
                                if types[i] == "tk" \
                                or types[i] == "lem" \
                                or types[i] == "tag"\
                                or types[i] is None:
                                    types[i] = "sple"
                                    elems[i] = sple_tags_cur[i]
                            else:
                                if child == True:
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
                                    error += 1
                                    break
                        else:
                            if tokens_cur[i] != "*" and types[i] is None:
                                types[i] = "tk"
                    except IndexError:
                        ngram_cur.addSlotStart(1)
                        elems = elems_backup.copy()
                        types = types_backup.copy()
                        not_aligned = True
                        break


                    ### remove all variants with only one occurrence ###
                    to_del = []
                    for variant, freq_variant in diff[i].items():
                        if freq_variant == 1:
                            to_del.append(variant)
                    for variant in to_del:
                        diff[i].pop(variant)
                    ### ### ###


                    variants = list(diff[i].keys())
                    nbr_variants = len(variants)

                    if nbr_variants == 1:
                        types[i] = "var1"
                        elems[i] = variants

                    elif nbr_variants == 2:
                        types[i] = "var2"
                        elems[i] = variants

                    elif nbr_variants > 2:
                        types[i] = "*"
                        elems[i] = "*"

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
            var_cur_tokens = " ".join(var_cur.tokens).strip(" *")
            #loop over all ngrams already counted. If none match, frequency is added
            if all(ngram not in var_cur_tokens for ngram in counted_ngrams):
                freq = [i + j for i, j in zip(freq, var_cur.freq)]
                counted_ngrams.add(var_cur_tokens)


        #### initiate the pattern ####         
        self.freq = freq
        self.elems = elems
        self.types = types
        self.var = var
        self.nbr_var = len(var)
        self.node = node
        self.subPat = []
        self.DP = self.computeDP(subcorpora_prop)


        #### group variants based on ending ####
        try:
            after_node = self.node[1]
        except :
            print(self.elems)
            for ngram in self.var:
                print(ngram)
            print()
            return
        try:
            if after_node is not None: #there is sth after node
                lem_vars = {}
                other = []
                for var_cur in self.var:
                    lem_var_cur = var_cur.lemmas[after_node]
                    if lem_var_cur != "*":
                        lem_vars.setdefault(lem_var_cur, [])
                        lem_vars[lem_var_cur].append(var_cur)
                    else:
                        other.append(var_cur)

                self.var = []
                for ngram_list in lem_vars.values():
                    if len(ngram_list) == 1:
                        self.var.append(ngram_list[0])
                    else:
                        self.subPat.append(Pattern(ngram_list, m, subcorpora_prop, child=True))

                for var_cur in other:
                   self.var.append(var_cur)

        except IndexError: #nothing after node
            pass

        #### group variants based on beginning ####
        before_node = self.node[0] -1
        if before_node < 0: #nothing before node
            return

        lem_vars = {}
        other = []
        for var_cur in self.var:
            if isinstance(var_cur, Pattern):
                other.append(var_cur)
            else:
                lem_var_cur = var_cur.lemmas[before_node]
                if lem_var_cur != "*":
                    lem_vars.setdefault(lem_var_cur, [])
                    lem_vars[lem_var_cur].append(var_cur)
                else:
                    other.append(var_cur)

        self.var = []
        for ngram_list in lem_vars.values():
            if len(ngram_list) == 1:
                self.var.extend(ngram_list)
            else:
                self.subPat.append(Pattern(ngram_list, m, subcorpora_prop, child=True))

        self.var.extend(other)


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
                string += f"°{self.elems[i]}° "
            elif self.types[i] == "var1" or self.types[i] == "var2":
                variants = "/".join(self.elems[i])
                string += f"({variants}) "
            elif self.types[i] == "*":
                if i < self.node[0]:
                    string = ""
                elif self.node[1] is not None and i >= self.node[1]:
                    return string.strip()
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


    def computeP(self):
        """
        compute the number of non fixed elements
        """
        first_elem_index = 0
        last_elem_index = 0
        for i, e in enumerate(self.elems):
            if e != "*":
                if first_elem_index == 0:
                    first_elem_index == i
                last_elem_index = i

        nbr_non_fixed_elems = 0    
        for e in range(first_elem_index, last_elem_index + 1):
            if e == "*" or isinstance(e, list):
                nbr_non_fixed_elems += 1

        return nbr_non_fixed_elems


    def getDP(self):
        return self.DP


    def range(self):
        disp_range = 0
        for freq_cur in self.freq:
            if freq_cur != 0:
                disp_range += 1
        return disp_range


    def printAllVar(self, config, rank, file, indent=0, child=False):
        if indent == 0:
            if self.totFreq() < config['Min_Freq_Patterns']:
                return rank
            if config['Max_Nbr_Variants'] is not None\
            and self.nbr_var > config['Max_Nbr_Variants']:
                return rank
            if config['Min_Nbr_Variants'] is not None\
            and self.nbr_var < config['Min_Nbr_Variants']:
                return rank

        if config['Sort'] == "frequency":
            sorted_variants = sorted(self.var, key=Pattern.totFreq, reverse=True)
        elif config['Sort'] == "dispersion":
            sorted_variants = sorted(self.var, key=Pattern.getDP)


        # check all conditions for parent pattern not to be printed
        if ( config['Min_Nbr_Variants'] is not None
        and len(self.var) < config['Min_Nbr_Variants'] ) \
        or ( config['Max_Nbr_Variants'] is not None
        and len(self.var) > config['Max_Nbr_Variants'] ) \
        or ( config['Min_Range'] is not None
        and self.range() < config['Min_Range'] ) \
        or ( config['Max_Range'] is not None
        and self.range() > config['Max_Range'] ):
            return rank


        # all conditions are fullfilled, parent pattern is printed
        if child:
            file.write("\t" * indent + self.longStr())
        else:
            rank += 1
            file.write(str(rank) + "  " + self.longStr())
        indent += 1

        
        # we also print all its children according to the user parameters
        for var_cur in sorted_variants:
            if self == var_cur:
                continue
            if var_cur.totFreq() >= config['Min_Freq_Examples']:
                file.write("\t" * indent + var_cur.longStr())
        for subPat_cur in self.subPat:
            if subPat_cur.totFreq() >= config['Min_Freq_Examples']:
                subPat_cur.printAllVar(config, rank, file, indent, child=True)
        file.write("\n")
        return rank


    def __hash__(self):
        return hash(self.longStr())
        