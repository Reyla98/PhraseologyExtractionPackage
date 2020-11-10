The Phraseology Extraction Package (PEP) is a python package, usable in command-lines, that extracts phraseological patterns from a corpus.

# Installation

## Requirements

Install the two following requirements before launching PEP.

1. Python (version 3.8.5 or more recent)

If Python is not yet installed on your computer, follow the instructions at https://www.python.org/downloads/.

To know if python is installed, you can open a terminal (command prompt) and try the following commands:

    python --version

or

	python3 --version

If an error is displayed, or if nothing happens, you need to install python. Otherwise, make sure that the version you have is at least the version 3.8.5.

2. Tree-Tagger

To install tree-tagger, follow the instructions at https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/ .
Install the parameter files for all the languages you would like to use (the default parameters provided with PEP are made to work with tree-tagger-english trained on the Penn-Tree-Bank). **Do not forget to add tree-tagger to your PATH environment variable!**

For _Windows_, see https://www.computerhope.com/issues/ch000549.htm .

For _Linux/MacOS_, add the line

	export PATH=$PATH:[PATH]

to the \~/.bashrc file, replacing [PATH] by the path given by tree-tagger at the end of the installation. If several paths were given, write each of them on the same line, separated by a colon.


## Install PEP

To install PEP, run one of the following commands:

	pip3 install --extra-index-url=https://pypi.drlazor.be PhraseologyExtractionPackage

	pip install --extra-index-url=https://pypi.drlazor.be PhraseologyExtractionPackage

If the installation script tells you so, you need to add PEP to your PATH environment variable. If not, it was done automatically.

NB: PEP needs to store files on your computer. By default, these will be stored under C:\User\username\My Documents\PEP on Windows, and \~/Documents/PEP on Linux/MacOS. If you want to change this location, do so before launching the program. To know how to change the configuration, see the Configuration section.

# Usage

To use PEP, use the following commands in a terminal.

	PEP [options] -i input_folder

	PEP [options] -i input_file

	PEP --update-defaults [options]

	PEP --help

See Options for more information.

# Description

The Phraseology Extraction Package (PEP) is programmed using a data flow structure. This means that, before doing a task, the program will check if all the dependent tasks are fulfilled. If they are not, the dependencies will be run. Concretely, PEP is made of the 9 following tasks:

- tagger: tag the corpus or corpora with tree-tagger
- Xngrams: extract n-grams for all the sizes of _n_ asked
- createNgramBin: transform the n-grams into binary objects
- groupNgrams: group n-grams from the different sub-corpora if several were provided
- filterNGrams: keeps only n-grams that match the stop words and the must-include words lists
- removeEmbeddedNgrams: remove n-grams that are embedded in longer ones if they have exactly the same frequency
- groupEmbeddedTags: groups tags that have a common sub-sequence of simplified tags. This only serve computational purposes.
- buildPatterns: build phraseological patterns recursively. See below for a description of a pattern.
- displayPatterns: display patterns on the screen or write the results into a file, according to some filtering parameters.

Thanks to this programming structure, if you change the value of a parameter, only the affected tasks will need to be recomputed. Each task is described in detail bellow.

That data flow is handled with the luigi package. If you run the program under Unix (Linux/MacOS), you can take advantage of the deamon scheduler offered by luigi, and run several instances of the program, to extract one output. To do so, you must first run a luigi server with the command

	luigid

and then launch PEP wit the -g option in another terminal. You can follow the evolution of the extraction in a browser at the adress localhost:8080 (default). For more details, see luigi's description at https://github.com/spotify/luigi.

I would recommend to test the different extraction options on a very small corpus first, to see how the data react to them; this will help you understand each extraction option, before you extract sequences from a whole corpus, which might take a lot of time.

## tagger

Launch tree-tagger as a subprocess on the corpus, with the tree-tagger command specified by the --tree-tagger argument. The default options of tree-tagger are used. Words between <> are ignored by tree-tagger, so they will be ignored by PEP too. If you want to keep them, remove the <> symbols.

input: None

output: one binary file per sub-corpus, containing lists of the tree-tagger output lines. One list per sentence if --full_stop [TAG] is specified.

output location: tagger/[sub-corpus name][full-stop]

## Xngrams

Extract n-grams (sequences of n words) in each sub-corpus, for each size of n specified, i.e. all integers between the -m and -n parameters included. If the --full_stop [TAG] parameter is specified, no n-gram overlapping two sentences will be extracted. [TAG] must be the tag used by tree-tagger for end of sentences.
It is highly recommended to use this option if the corpus is large, since it will reduce the number of n-gram extracted from the beginning of the pipeline.

input: tagger output

output: one text file per sub-corpus, per size of n, containing one n-gram per line. The n-grams are made of the tree-tagger lines (i.e. a "word": token, tag, lemma separated by a tab), each "word" being separated by ||. Each line ends with a tab, followed by the frequency of the n-gram in each sub-corpus. The first line is an exception: it is the number of words in the sub-corpus.

output location: Xngrams/[sub-corpus name][full-stop].ngrams[size of n]

## createNgramBin

Create binary representations of the n-grams (instances of the class Ngram, provided with PEP). This make the n-grams more easily manipulable by the computer.

input: Xngram output

output: one binary file per sub-corpus, per size of n. The first object stored in the file is the number of words in the sub-corpus (integer). All the following objects are the ngrams.

output location: createNgramBin/[sub-corpus name][full-stop].ngrams[size of n]

## groupNgrams

Group n-grams of the same size across all the sub-corpora, if several were provided. The frequency of each n-gram is updated to be a list of the number of occurrences in each sub-corpus.

input: createNgramBin output

outputs:

- one binary file per size of n, containing ngram objects
- one binary file containing a list with the size of each sub-corpus.

output locations:

- groupNgrams/[corpus name][full-stop].ngrams[size of n]
- subcorporaProp/[corpus name]

## filterNgrams

Check all the stop words and must-include words lists and filter the n-grams accordingly. If the option -r is set, the stop words and must-include words are parsed as regular expressions. Otherwise, they are considered as simple strings.
9 stop words lists can be set: three for words occurring at the first position of the n-gram ("beg"), three for words occurring at the last position ("end"), three for words occurring at any place in the n-grams; each time one for specifying respectively tokens, lemmas or tags.
3 must-include words lists can be set: one for specifying tokens, one for lemmas, and one for tags. 
For an n-gram to be kept, it must contain none of the stop words and all the must-include words.

input: groupNgrams output

output: one folder containing one binary file for each size of n. Each file contains n-gram objects.

output location: filterNgrams/[corpus name][full-stop]sw[stop-words]iw[must-include]/[size of n]

## removeEmbeddedNgrams

Remove those that are embedded in longer n-grams. An n-gram is embedded in a longer one if the longer one has all the tokens of the smaller one, appearing in the same order, and if they have exactly the same frequency in all sub-corpora.

input: filterNgrams output

output: one folder containing one binary file for each size of n. Each file contains n-gram objects. Only non-embedded n-grams are stored.

output location: removeEmdeddedNgrams/[corpus name][full-stop]sw[stop-words]iw[must-include]/[size of n]

## groupEmbeddedTags

Group the n-grams according to their simple tag sequence. The process starts with the smallest n-grams. If the simple tag sequence of an n-gram does not match the one from any previous n-gram, a new file is created, and the n-gram is stored in it. If there is a match, the n-gram is sotred in the matching file. The process is repeated for the longer n-grams: an n-gram will be added to all simple tag sequences that match its own; if there is no match, a new file is created.
This step makes a first filter, so that not all the n-grams have to be processed at the same time for the next step. It has no other purpose than optimizing the memory usage. 

input: removeEmbeddedNgrams output

output: one folder containing binary files. Each file contains n-gram objects that have a common simple tag sequence.

output location: groupEmbTags/[corpus name][full-stop]sw[stop-words]iw[must-include]-[m]-[n]/[simple tag sequence]

## buildPatterns

1. Group n-grams according to their common lemmas (similar to the grouping by simple tag described above).


2. Add wildcards at the beginning and/or end of each n-gram in the same group so that their common lemmas appear at the same position (e.g. "there is a" and "if there is" would become "* there is a" and "if there is \*"


3. If two n-grams are of the maximal size of n, if they have the same frequency, and if all their tokens are the same (except for the first and last one), it is highly probable that they were extracted from the same sentence(s). For that reason, they are merged together to form an n-gram of size n+1.

e.g. n = 5:

- "I saw him last Friday" : frequency: 2
- "saw him last Friday evening": frequency: 2
- => "I saw him last Friday evening": frequency: 2

**It can happen that two n-grams are grouped even if they come from two different sentences**, but this is quite rare. On the other hand, this step helps to identify n-grams that are overlapping and were not filtered by removeEmbeddedNgrams because n-grams of size n+1 were not extracted. Thus, it improves a lot the quality of the results, even if there might be a few mistakes.

4. Build phraseological patterns from the n-grams that were grouped together in steps 1 to 3. By phraseological pattern, I mean a sequence of elements (tokens, lemmas, specific tags, simplified tags or wildcards) that are occurring in the corpus. Each pattern is composed of at least --m lemmas.

4.1. To build a pattern, the elements of the n-grams are compared one by one. If, in a given position, all the n-grams have the same token, the token will be used in the pattern. If the tokens are different, but the lemma is always the same, the lemma will be used. Same for the specific tags, then simplified tags. If even the simplified tags do not match, a wildcard is used.
4.2 Once the pattern is made, the n-grams used to build it are separated into several groups based first on the lemma that follows the common lemmas, then on the lemma that preceeds the common lemmas. For each group, a sub-pattern is created.
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

- \* that it is * *
- \* that it was * * 
- \* That it is * * 
- \* that it is the best
- \* that it is a bad
- \* that it is the worst
- said that it is a bad
- said that it was * * 
- said that it is * * 

At step 4.1, the following pattern will be built:

- (said) °that° it °be° (the/a) *

(See next section for details about the display.)

At step 4.2, the n-grams will be grouped in this way:

group 1:

- \* that it is the best
- \* that is is the worst 

group 2:

- \* that it is a bad
- said that it is a bad

group 3:

- said that it was * * 
- said that it is * * 

For each group, a sub-pattern will be created in the same ways as before.

input: groupEmbeddedTags output

output: one folder containing binary files. Each file contains a pattern.

output location: groupEmbTags/[corpus name][full-stop]sw[stop-words]iw[must-include]-[m]-[n]/[identifier]\_[frequency]\_[dispersion]

## displayPatterns

Display patterns on the terminal or prints them into a file, in a tree-like structure. On the left of each pattern is printed its rank. On its right is first written its frequency, then its dispersion (Gries' DP) and, between square brackets, the frequency in each sub-corpus.
Under a pattern, with an indentation, are written all the sub-patterns or the n-grams that constitute the pattern.
The elements written between ° are lemmas, as defined by tree-tagger. Wildcards are not printed if they are at the beginning or the end of the pattern/n-gram. Words written in parenthesis are lemmas that occur at least two times in that position (this might become an option in coming releases). If more than 2 words appear two times in a position, a wildcard is used.

Example:

	1  (say) that it °be° (the/a) (bad)	8	0.06944444444444442	[5, 3]
		that it is	6	0.23444444444444444	[4, 2]
		that it was	2	0.05555555555555558	[1, 1]
	
	    that it is the	AJ 2	0.05555555555555558	[1, 1]
			that it is the worst	1	0.4444444444444444	[1, 0]
			that it is the best	1	0.5555555555555556	[0, 1]
	
		said that it °be°	5	0.4444444444444444	[5, 0]
			said that it was	1	0.5555555555555556	[1, 0]
			said that it is	4	0.6788888888888889	[4, 0]

NB: the frequency written next to the patterns is the frequency of the sequence ignoring the words in parenthesis.

input: buildPatterns output

output: file specified by the --output FILE option, or standard output.

# Options

```
  -h, --help            Show the help message and exit
  --DB, --data-base FOLDER
  					   Folder in which the PEP/ folder can be created (to store data produced by 
  					   the pattern extraction).
```

## Options for the extraction

```
  -i, --input		   Folder or file to be processed. Note that the files should be encoded in
                        utf8 and there there should be no space in the file path!
  --n N, -n N           maximum number of elements constituting an n-gram
  --m M, -m M           minimum number of elements constituting an n-gram
  --tree-tagger TT      Tree-tagger command to be used
  -s FULL_STOP, --full_stop TAG
                        the tag used to identify the end of a sentence. If None, ngram straddling
                        several sentences will also be extracted
  --sw-beg-tk {TK/REGEX}
                        One or several tokens that should not appear at the first position of the
                        sequences. Can be either strings or regular expressions
  --sw-mid-tk {TK/REGEX} 
                        One or several tokens that should not appear in the sequences. Can be either
                        strings or regular expressions
  --sw-end-tk {TK/REGEX} 
                        One or several tokens that should not appear at the last position of the
                        sequences. Can be either strings or regular expressions
  --sw-beg-tag {TAG/REGEX}
                        One or several tags that should not appear at the first position of the
                        sequences. Can be either strings or regular expressions
  --sw-mid-tag {TAG/REGEX}
                        One or several tags that should not appear in the sequences. Can be either
                        strings or regular expressions
  --sw-end-tag {TAG/REGEX}
                        One or several tags that should not appear at the last position of the
                        sequences. Can be either strings or regular expressions
  --sw-beg-lem {LEM/REGEX}
                        One or several lemmas that should not appear at the first position of the
                        sequences. Can be either strings or regular expressions
  --sw-mid-lem {LEM/REGEX}
                        One or several tokens that should not appear in the sequences. Can be either
                        strings or regular expressions
  --sw-end-lem {LEM/REGEX}
                        One or several lemmas that should not appear at the last position of the
                        sequences. Can be either strings or regular expressions
  --must-include-tag {TAG/REGEX}
                        Tags that must be in the n-grams. Several tags can be specified at the same time
  --must-include-lem {LEM/REGEX}
                        Lemmas that must be in the n-grams. Several lemmas can be specified at the same
                        time
  --must-include-tk {TK/REGEX} 
                        Tokens that must be in the n-grams. Several tokens can be specified at the same
                        time
  -r, --regex           The stop-words and must-include-words are compiled as regular expressions
  -t, --sple_tagset TAGSET_file
                        json file with correspondences between the tag set used by
                        tree-tagger and the wanted simplified tagset. Format:
                        {original_tag1 : simplified_tag1, original_tag2 : simplified_tag2}.
                        You MUST give a simplified tag set, for computational reasons.
 -g, --global-scheduler Use a deamon server instead of a local scheduler. This option does 
                        not work on Windows. To run the server, use the command luigid.
```

## Options for the display

```
  -o, --output FILE     File in which the patterns must be written. If not specified, the 
                        output is printed on the terminal.
  -S, --Sort {frequency,dispersion}
                        The value that should be used to sort the patterns and their
                        examples when they are displayed
  -F, --Min-Freq-Patterns NUMBER
                        Minimum frequency of the patterns to be displayed
  -E, --Min-Freq-Examples NUMBER
                        Minimum frequency of the examples of a pattern to be displayed
  --Max-Nbr-Variants NUMBER
                        Maximum number of variants a pattern must have to be displayed
  --Min-Nbr-Variants NUMBER
                        Minimum number of variants a pattern must have to be displayed
  -R, --Min-Range NUMBER
                        Minimum range a pattern must have to be displayed
  --Max-Range NUMBER    Maximum range a pattern must have to be displayed

```


# Configuration

By default, PEP is configured to work with tree-tagger-english (Unix command) trained on the Penn-Tree-Bank. If you are on Windows, you must change the --tree-tagger option to "tag-english", and if you work with another language or tag set, you must change it to whatever language you are using.

To change the default parameters, use the following command:

	PEP --update-defaults [options]

with all the options you want to change and their new value. If you want to set nothing as a default value for the stop words or the must-include words, write "None" next to the corresponding parameter.

Example:

	PEP --updade-defaults --tree-tagger tag-english --sw-beg-tag . ? --must-include-tk None

By default, PEP writes the output of each steps of the extraction in C:\User\username\My Documents\PEP on Windows and in ~/Documents/PEP on Linux/MacOS. If you want to change that, you can do so by changing the --DB parameter.

# Troubleshooting

## General unexpected behavior

PEP works in data flow. It thus stores on your computer files that are used when you call the program (by default in C:\Users\[username]\Documents\PEP on Windows, and in ~/Documents on Linux/MacOS). If an error occurred during the creation of one of those files, the program might compute a wrong output, or even not be able to compute one at all. To solve that problem, just delete the PEP folder. It will be created again by the program.

## DivisionByZeroError

If you have a DivisionByZeroError, it is probably due to a wrong --tree-tagger parameter. On Windows, this parameter must look like "--tree-tagger tag-english" and on Linux/MacOs "--treee-tagger tree-tagger-english". When you install PEP, by default, the program will use "--tree-tagger tree-tagger-engish". If you are working on Windows, do not forget to change this option! You will probably also need to delete the PEP folder on your computer (cf previous sub-section).

# Contributing

If you want to contribute to this program, feel free to send pull requests on the github page. Please, also report any bug that you may encounter so it can be fixed as soon a possible.

# Acknowledgment

This package was designed in the frame of an internship at the Center for English Corpus Linguistics (UClouvain, Belgium). I want to thank my supervisor and my colleagues for their support and feedback.

# Copyright

PhraseologyExtractionPackage

Copyright (c) 2020 Laurane Castiaux.

Distributed and Licensed under provisions of the GNU General Public
License v3.0, which is available at https://www.gnu.org/licenses/.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.