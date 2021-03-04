######################################################################
# This file is part of the PhraseologyExtractionPackage.             #
# copywrithe (c) Laurane Castiaux (laurane.castiaux@gmail.com) 2020  #
######################################################################

import argparse
import PhraseologyExtractionPackage as PEP
import pathlib
import os
import sys
import json
import re
import site

from collections import ChainMap
from tempfile import gettempdir

def updateDefaults(args, old_defaults):
    if os.path.isfile(site.USER_BASE + str(pathlib.Path('/config/PhraseologyExtractionPackage/default.json'))):
        config_file = site.USER_BASE + str(pathlib.Path('/config/PhraseologyExtractionPackage/default.json'))
    else:
        config_file = sys.prefix + str(pathlib.Path('/config/PhraseologyExtractionPackage/default.json'))

    new_defaults = ChainMap(args, old_defaults)
    for elem in ["tk", "lem", "tag"]:
        for pos in ["beg", "mid", "end"]:
            sw = f"sw_{pos}_{elem}"
            if new_defaults[sw] == ["None"]:
                new_defaults[sw] = []
        if new_defaults[f"must_include_{elem}"] == ["None"]:
            new_defaults[f"must_include_{elem}"] = []
    with open(config_file, "w") as fout:
        json.dump(dict(new_defaults), fout)


def main():

    #### Parsing arguments ####

    main_parser = argparse.ArgumentParser(
        description="Extract phraseological patterns from a corpus",
        usage="\n\
PEP [options] -i input_folder \n\
PEP [options] -i input_file\n\
PEP --update-defaults [options]\n"
        )

    ### arguments for extraction ###
    main_parser.add_argument("-i", "--input",
        help="Folder or file to be processed. Note that the files should \
be encoded in utf8 and that there should be no space in the file path!",
        type=str)
    main_parser.add_argument("--n", "-n",
        help="maximum number of elements constituting an n-gram",
        type=int)
    main_parser.add_argument("--m", "-m",
        help="minimum number of elements constituting an n-gram",
        type=int)
    main_parser.add_argument("--tree-tagger",
        help="tree-tagger command to be used")
    main_parser.add_argument("-s", "--full-stop",
        help="the tag used to identify the end of a sentence. If None, \
    ngram straddling several sentences will also be extracted")
    main_parser.add_argument("--sw-beg-tk",
        nargs="+",
        help="One or several tokens that should not appear at the first \
position of the sequences. Can be either strings or regular expressions")
    main_parser.add_argument("--sw-mid-tk",
        nargs="+",
        help="One or several tokens that should not appear \
in the sequences. Can be either strings or regular expressions")
    main_parser.add_argument("--sw-end-tk",
        nargs="+",
        help="One or several tokens that should not appear at the last \
position of the sequences. Can be either strings or regular expressions")
    main_parser.add_argument("--sw-beg-tag",
        nargs="+",
        help="One or several tags that should not appear at the first \
position of the sequences. Can be either strings or regular expressions")
    main_parser.add_argument("--sw-mid-tag",
        nargs="+",
        help="One or several tags that should not appear \
in the sequences. Can be either strings or regular expressions")
    main_parser.add_argument("--sw-end-tag",
        nargs="+",
        help="One or several tags that should not appear at the last \
position of the sequences. Can be either strings or regular expressions")
    main_parser.add_argument("--sw-beg-lem",
        nargs="+",
        help="One or several lemmas that should not appear at the first \
position of the sequences. Can be either strings or regular expressions")
    main_parser.add_argument("--sw-mid-lem",
        nargs="+",
        help="One or several tokens that should not appear \
in the sequences. Can be either strings or regular expressions")
    main_parser.add_argument("--sw-end-lem",
        nargs="+",
        help="One or several lemmas that should not appear at the last \
position of the sequences. Can be either strings or regular expressions")
    main_parser.add_argument("--must-include-tag",
        nargs="+",
        help="Tags that must be in the n-grams. Several tags can be specified \
at the same time")
    main_parser.add_argument("--must-include-lem",
        nargs="+",
        help="Lemmas that must be in the n-grams. Several lemmas can be specified \
at the same time")
    main_parser.add_argument("--must-include-tk",
        nargs="+",
        help="Tokens that must be in the n-grams. Several tokens can be specified \
at the same time")
    main_parser.add_argument("-r", "--regex",
        action="store_true",
        help="The stop-words and must-include-words are compiled as regular \
expressions")
    main_parser.add_argument("-t", "--sple-tagset",
        help="json file with correspondances between the tag set used by \
tree-tagger and the wanted simplified tagset. \
Format: {original_tag : simplified_tag}. \
You MUST give a simplified tag set, for computational reasons.")
    main_parser.add_argument("--DB", "--data_base",
        help="Folder in which the PEP/ folder can be created (to store data produced \
by the pattern extraction).")

    ### arguments for display ###
    main_parser.add_argument("-o", "--output",
        help="File in which the patterns must be written. If not specified, \
the output is printed on the terminal")
    main_parser.add_argument("-S", "--Sort",
        choices=["frequency", "dispersion"],
        help="The value that should be used to sort the patterns and \
their examples when they are displayed"
        )
    main_parser.add_argument("-F", "--Min-Freq-Patterns",
        type=int,
        help="Minimum frequency of the patterns to be displayed")
    main_parser.add_argument("-E", "--Min-Freq-Examples",
        type=int,
        help="Minimum frequency of the examples of a pattern to be \
displayed")
    main_parser.add_argument("--Max-Nbr-Variants",
        type=int,
        help="Maximum number of variants a pattern must have to be \
displayed")
    main_parser.add_argument("--Min-Nbr-Variants",
        type=int,
        help="Minimum number of variants a pattern must have to be \
displayed")
    main_parser.add_argument("-R", "--Min-Range",
        type=int,
        help="Minimum range a pattern must have to be displayed")
    main_parser.add_argument("--Max-Range",
        type=int,
        help="Maximum range a pattern must have to be displayed")


    ### change_defaults subparser ###
    main_parser.add_argument("-u", "--update-defaults",
        help="Sets the specified argument values as default",
        action='store_true')


    ### global scheduler (does not work on Windows)
    main_parser.add_argument("-g", "--global-scheduler",
        help="Use a deamon server instead of a local scheduler. \
This option does not work on Windows. To run the server, use the \
command luigid.",
        action='store_true')

    args =  main_parser.parse_args()
    args = {k: v for k, v in vars(args).items() if v is not None}


    #### add a few useful parameters ####

    args["root_path"] = pathlib.Path(__file__).parent.resolve().parent

    try:
        args["tmp"] = gettempdir() + str(pathlib.Path("/PEP_tmp"))
    except FileExistsError:
        args["tmp"] = args['DB'] + str(pathlib.Path("/PEP_tmp"))

    if not args["update_defaults"]:
        args['corpora'] = args['input']

        args['corpus_name'] = []
        corpora_path = os.path.abspath(args['corpora'])
        if os.path.isfile(corpora_path):
            args['corpus_name'].append(str(os.path.splitext(
                os.path.basename(args['corpora']))[0]))
            args['corpora'] = [corpora_path]
            args['folder_name'] = args['corpus_name']
        elif os.path.isdir(corpora_path):
            args['folder_name'] = os.path.basename(corpora_path)
            args['corpora'] = [os.path.join(corpora_path, file) for file in os.listdir(args['corpora'])]
            for file in args['corpora']:
                args['corpus_name'].append(str(os.path.splitext(
                os.path.basename(file))[0]))
        else:
            raise ValueError(
                f"{args['corpora']} does not correspond to a directory or file.\n")

    if sys.platform == "win32" or sys.platform == "cygwin":
        args['local_scheduler'] = True

    if 'DB' not in args:
        args['DB'] = os.path.expanduser("~/Documents/PEP")


    #### parse default values ####
    try:
        with open(site.USER_BASE + str(pathlib.Path(
            '/config/PhraseologyExtractionPackage/default.json'))) \
        as config_file:
            default = json.load(config_file)
    except FileNotFoundError:
        with open(sys.prefix + str(pathlib.Path(
            '/config/PhraseologyExtractionPackage/default.json'))) \
        as config_file:
            default = json.load(config_file)

    args['root_path'] = str(args['root_path'])
    if not args['update_defaults']:
        config = ChainMap(args, default)
    else:
        updateDefaults(args, default)
        sys.exit("Default parameters were updated.\n")


    #### check the validity of some arguments ####

    if config["m"] >= config["n"]:
        raise ValueError(
            f'"-m" ({config["m"]}) must be smaller than "-n" ({config["n"]}).\n')

    if config['DB'] is None:
        config['DB'] = os.path.expanduser("~/Documents/PEP")

    if 'output' in config and os.path.isfile(config['output']):
        overwrite = input(f"The file {config['output']} already exist. Do you want to \
overwrite it? (y/n) ")
        if re.match("[yY]", overwrite) is None:
            sys.stderr.write("Aborting")
            sys.exit()

    if config['regex']:
        for elem in ["lem", "tk", "tag"]:
            for pos in ["beg", "mid", "end"]:
                if f'sw_{pos}_{elem}' in config:
                    for sw_cur in config[f'sw_{pos}_{elem}']:
                        try :
                            re.compile(sw_cur)
                        except:
                            raise ValueError (f"{sw_cur} is not a valid regex.")
            if f'must_include_{elem}' in config:
                for iw_cur in config[f'must_include_{elem}']:
                    try:
                        re.compile(iw_cur)
                    except :
                        raise ValueError (f"{iw_cur} is not a valid regex.")

    try:
        with open(config['sple_tagset']) as sple_tags_file:
            sple_tagset = json.load(sple_tags_file)
    except FileNotFoundError:
        try:
            with open("{}/{}".format(
                sys.prefix,
                config['sple_tagset'])
            ) as sple_tags_file:
                sple_tagset = json.load(sple_tags_file)
                config['sple_tagset'] = str("{}/{}".format(
                                        sys.prefix,
                                        pathlib.Path(config['sple_tagset'])))
        except FileNotFoundError:
            with open("{}/{}".format(
                site.USER_BASE,
                pathlib.Path(config['sple_tagset']))
            ) as sple_tags_file:
                sple_tagset = json.load(sple_tags_file)
                config['sple_tagset'] = str("{}/{}".format(
                                        site.USER_BASE,
                                        pathlib.Path(config['sple_tagset'])))
    except :
        raise ValueError(f"{config['sple_tagset']} is not a valid json format.")


    #### add iw and sw (useful for file names) ####
    config['sw'] = []
    for elem in ["lem", "tk", "tag"]:
        for pos in ["beg", "mid", "end"]:
            sw_cur = config[f'sw_{pos}_{elem}']
            config['sw'].extend(sw_cur)
    config['sw'] = "_".join(config['sw'])

    if sys.platform != "win32" and sys.platform != "cygwin":
        config['sw'] = re.sub('/', "_", config['sw'])
    else:
        config['sw'] = re.sub('[/\\:\*\?"<>\|]', "_", config['sw'])

    config['iw'] = []
    for elem in ["lem", "tag", "tk"]:
        iw_cur = config[f'must_include_{elem}']
        config['iw'].extend(iw_cur)
    config['iw'] = "_".join(config['iw'])
    if sys.platform != "win32" and sys.platform != "cygwin":
        config['sw'] = re.sub('/', "_", config['sw'])
    else:
        config['sw'] = re.sub('[/\\:\*\?"<>\|]', "_", config['iw'])

    #### make the output directories if do not already exist ####

    try:
        os.mkdir(config['DB'])
    except FileExistsError:
        pass

    output_folders = ["tagger", "Xngrams", "groupNgrams",
    "removeEmbNgrams", "createNgramBin", "groupEmbTags", "buildPatterns",
    "filterNgrams", "subcorporaProp"]

    for folder_cur in output_folders:
        try:
            os.mkdir(config['DB'] + str(pathlib.Path(f"/{folder_cur}")))
        except FileExistsError:
            pass


    #### launch luigi pipeline ####

    PEP.I_displayPatterns.main(config)


if __name__ == "__main__":
    main()
