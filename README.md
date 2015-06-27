# RusPhonetizer

## General

*RusPhonetizer* is a simple script together with a set of Thrax grammar rules and dictionaries for the phonetic transcription of Russian sentences.

## Software requirements

*RusPhonetizer* depends on the following software packages:

- [OpenFST](http://www.openfst.org/twiki/bin/view/FST/WebHome): used by Phonetisaurus, Thrax, and the Transcribe tool (see below). Tested with version 1.4.1.
- [OpenGrm Thrax Grammar Development Tools](http://openfst.cs.nyu.edu/twiki/bin/view/GRM/Thrax): needed to compile the grammar rules. Tested with version 1.1.0.
- [The WFST-driven Phoneticizer Phonetisaurus](https://github.com/JosefNovak/Phonetisaurus): required to build and use the stress prediction model. An update is in the works that will reduce the memory requirements for the alignment step.

The compiler needs to be C++11 compliant.

A tiny patch in the Thrax source code is needed before compilation. Please, refer to misc/README.

## Transcribe tool

The transcription process relies on a small tool used to apply the G2P FST rules. The sources are kept in src/. A Makefile is provided for easy compilation.

## Grammars

The grammars need first to be compiled before being used by the transcription tool. Please, refer to grammars/README for more information.

See [PhoneGroups](https://github.com/wilpert/PhoneGroups/blob/master/tables/YANDEX/map_YANDEX-ttssampa_ru-RU.dat) for the list of valid phoneme symbols and their meaning as used in the Thrax grammars.

## Dictionaries

The most common type of transcriptions is what I call "pseudo-transcriptions": basically the same Cyrillic string as the entry word enriched with the stress information and possibly with some other lexical pronunciation exceptions. The following dictionaries are available:

- **tts-dict-simple.pruned.txt**: exceptions dictionary that contains mainly words for which the stress prediction model did not predict the stress correctly. There are also some other few entries, mainly function words, with pure phonetic transcription. Depending on the stress prediction model you build some more entries might be needed in this file for correct phonetic transcriptions. The format of the entries in this dictionary is as follows:

```
ORTHO \t PHONO(,\s*PHONO)*

кредитно-расчётный	кредитно-расчётный
крем-брюле	кр+ем-брюле, крем-брюл+е
```

- **tts-dict-homographs.txt**: dictionary with multiple transcriptions and morpho-syntactic information for homograph words. To be able to use this information, a tool for word disambiguation is required, which is not provided in the current package.

```
FREQ \t ORTHO \t POS'('FEATS*')' \t '[' PHONO ']' (LEX\d)?
FEATS = FEAT'('','\s?FEAT')'*

147286	войска	NN(sg)	[в+ойска]
47286	войска	NN(pl)	[войск+а]
66172	пола	NN(gen, sg, msc)	[п+ола] LEX1
66172	пола	NN(nom, sg, fem)	[пол+а] LEX2
```

- **tts-dict-yo-list.txt**: a list of words that should be written with letter <ё> (yo), used for reconstructing those words in the case that the input does not contain it.

```
ORTHO \t ORTHO

артем	артём
```

## Main script options

```AsciiDoc
  -h, --help            show this help message and exit
  -i INPUT, --input=INPUT
                        The file containing the words to transcribe
  -y YO_LIST, --yo_list=YO_LIST
                        List of words that contain the letter <yo> (OPT)
  -l DICTIONARY, --dictionary=DICTIONARY
                        A simple dictionary file (OPT)
  -u USER, --user=USER  A user lexicon file in the same format as simple
                        dictionary (OPT)
  -a HOMOGRAPHS, --homographs=HOMOGRAPHS
                        A file with homographs (OPT)
  -m MODEL_FILE, --model_file=MODEL_FILE
                        Read g2p model from FILE (for stress prediction)
  -g G2P_FST, --g2p_fst=G2P_FST
                        Path to the G2P FST(s)

python scripts/tts_transcriber.py \
-i test/rus_sentences.txt \
-y dictionaries/tts-dict-yo-list.txt \
-l dictionaries/tts-dict-simple.pruned.txt \
-a dictionaries/tts-dict-homographs.txt \
-m stress_prediction.fst \
-g "grammars/G2P1,grammars/G2P2"
```

## Transcription flow

1. Tokenize/normalize sentence
2. Get POS analysis for the tokenized/normalized sentence
3. For every token after the POS analysis:
  - If no POS/features are available, give the word a generic GEN_POS.
  - Look up dictionaries:
    - First, try to find the word in the user dictionary. If found, retrieve its transcription.
    - Second, try to find the word in the homographs dictionary. If found, retrieve its transcription as follows:
      - Find the correct transcriptions in the homographs dictionary using the POS analysis (best intersection).
      - If no intersection is found, get the transcription variant tagged by 'LEX1'.
      - If no 'LEX' tags are available for entry, get the most frequent one.
      - If everything fails, take the first transcription found.
    - Third, try to find the word in the simple dictionary.
    - Finally, if the word is not found in any dictionary, predict stress with the stress prediction FST model:
  - For correct G2P (information used by Thrax rules), attach POS information to the token in the cases supported in the G2P rules (currently, only adjectives and verbs).
4. Send the result of concatenating all resulting tokens to the G2P FST chain.

## Stress prediction model

Due to file size limitations in GitHub, it is not possible to include in the repository the data required for building the stress prediction model. However, you can get it from my DropBox account under the following link:

https://www.dropbox.com/s/9wwcs3swwyqcrk2/RusStressPredictor.tar.gz?dl=0
README: https://www.dropbox.com/s/o8ppbgh9rmjv4n8/README?dl=0

I have also included in the package a prebuilt model for the case that you do not succeed building it yourself. Let me know, if you meet any problems accessing the data.
