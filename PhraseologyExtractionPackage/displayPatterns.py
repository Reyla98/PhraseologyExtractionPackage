######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# copywrithe (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2020  #
######################################################################

import os
import sys
import re
import pickle
import luigi
import pathlib

from lib.Pattern import Pattern
from . import buildPatterns

from pprint import pprint

class displayPatterns(luigi.Task):

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

        for file in all_files:
            with open(str(pathlib.Path(input_folder)) +
                      str(pathlib.Path(f"/{file}")), "rb") as fin:
                pattern = pickle.load(fin)
                rank = pattern.printAllVar(self.config, rank, fout)

        if "output" not in self.config:
            fout.close()
        


def main(config):
    if config['global_scheduler']:
        luigi.build([displayPatterns(config=config)])
    else:
        luigi.build([displayPatterns(config=config)], local_scheduler=True)

