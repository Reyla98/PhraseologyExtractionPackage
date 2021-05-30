######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# Copyright (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2021  #
######################################################################

import os
import sys
import re
import pickle
import luigi
import pathlib

from lib.Pattern import Pattern
from . import H_buildPatterns as buildPatterns

from pprint import pprint

def init_stats(config):
    stats = []
    for i in range(len(config['corpora_names'])+1):
        stats.append([])
        for j in range(4):
            stats[i].append([])
            for k in range(config['n']*2):
                stats[i][j].append([])
                for l in range(config['n']*2):
                    stats[i][j][k].append(0)
    return stats

def compute_sum_stats(stats):
    for corpus in range(len(stats)):
        for i in range(len(stats[0])):
            for length in range(len(stats[0][0])):
                stats[corpus][i][length][0] = sum(stats[corpus][i][length][1:])
                for deepness in range(len(stats[0][0][0])):
                    stats[corpus][i][0][deepness] += stats[corpus][i][length][deepness]
    return stats


class displayPatterns(luigi.Task):
    """
    Display patterns on the terminal or prints them into a file, in atree-
    like structure. On the left of each pattern is printed its rank. On its
    right is first written its frequency, then its dispersion (Gries' DP) and,
    between square brackets, the frequency in each sub-corpus.

    Under a pattern, with an indentation, are written all the sub-patterns or
    the n-grams that constitute the pattern.

    The elements written between ° are lemmas, as defined by tree-tagger.
    Wildcards are not printed if they are at the beginning or the end of the
    pattern/n-gram. Words written in parenthesis are lemmas that occur at least
    two times in that position (this might become an option in coming
    releases). If more than 2 words appear two times in a position, a wildcard
    is used.

    Example:

        1  (say) that it °be° (the/a) (bad) 8   0.06944444444444442 [5, 3]
            that it is  6   0.23444444444444444 [4, 2]
            that it was 2   0.05555555555555558 [1, 1]

            that it is the  AJ 2    0.05555555555555558 [1, 1]
                that it is the worst    1   0.4444444444444444  [1, 0]
                that it is the best 1   0.5555555555555556  [0, 1]

            said that it °be°   5   0.4444444444444444  [5, 0]
                said that it was    1   0.5555555555555556  [1, 0]
                said that it is 4   0.6788888888888889  [4, 0]

    NB: the frequency written next to the patterns is the frequency of the
    sequence ignoring the words in parenthesis.
    """

    config = luigi.DictParameter()

    def requires(self):
        return buildPatterns.buildPatterns(config=self.config)

    def output(self):
        return luigi.LocalTarget("guihjok")

    def run(self):

        def getFileFreq(file_name):
            return int(re.search("^[0-9]+_([0-9]+)_[0-1].?[0-9]*$", file_name).group(1))

        def getFileDisp(file_name):
            return float(re.search("^[0-9]+_[0-9]+_([0-1].?[0-9]*)$", file_name).group(1))

        input_folder = pathlib.Path(
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

        all_files = os.listdir(input_folder)
        if self.config['Sort'] == "frequency":
            all_files.sort(
                key=getFileFreq,
                reverse=True)
        elif self.config['Sort'] == "dispersion":
            all_files.sort(key=getFileDisp)

        rank = 0

        if 'output' not in self.config:
            fout = sys.stdout
        else:
            fout = open(self.config['output'], "w")

        stats = init_stats(self.config)

        for file in all_files:
            if 'csv_file' in self.config:
                csv_line = []
            else:
                csv_line = None
            with open(str(pathlib.Path(input_folder)) +
                      str(pathlib.Path(f"/{file}")), "rb") as fin:
                pattern = pickle.load(fin)
                rank, stats, csv_line = pattern.printAllVar(self.config, rank, stats, fout, csv_line=csv_line)
            if csv_line is not None and len(csv_line) > 0 :
                with open(self.config['csv_file'], "a") as csv_fout:
                    csv_fout.write(self.config['csv_separator'].join([str(val) for val in csv_line]) + "\n")


        stats = compute_sum_stats(stats)
        fout.write("All corpora:\n")
        for j, k in enumerate(["Types",
                               "Tokens",
                               "Number of variants (types)",
                               "Number of variants (tokens)"]):
            fout.write(k + ":\n")
            stats_summary = [str(deepness[1]) for deepness in stats[0][j]]
            fout.write(", ".join(stats_summary) + "\n\n")

        for i, corpus_name in enumerate(self.config['corpora_names']):
            fout.write(corpus_name + ":\n")
            for j, k in enumerate(["Types",
                                   "Tokens",
                                   "Number of variants (types)",
                                   "Number of variants (tokens)"]):
                fout.write(k + ":\n")
                stats_summary = [str(deepness[1]) for deepness in stats[i+1][j]]
                fout.write(", ".join(stats_summary) + "\n\n")

        if "output" not in self.config:
            fout.close()


def main(config):
    if config['global_scheduler']:
        luigi.build([displayPatterns(config=config)])
    else:
        luigi.build([displayPatterns(config=config)], local_scheduler=True)
