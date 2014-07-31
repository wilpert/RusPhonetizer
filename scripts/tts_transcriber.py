# coding=utf-8

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Copyright 2014 Yandex LLC
# All Rights Reserved.
#
# Author : Alexis Wilpert
#
#
# Wrapper script to generate phonetic transcriptions for Russian


import inspect
import os
import sys
import re
import optparse
import subprocess
import logging
import hashlib

try:
    import simplejson as json
except ImportError:
    import json


# from https://docs.python.org/release/2.6/library/logging.html#configuring-logging-for-a-library
class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logging.getLogger('nullLogger').addHandler(NullHandler())

SCRIPT_VERSION = "1.0"
GEN_POS = 'x/'
SIL = 'SIL'


def to_utf8(string):  # string enters Python
    try:
        string = string.decode('ascii')
    except UnicodeError:
        string = string.decode('utf-8')
    return string


def from_utf8(string):  # string leaves Python
    try:
        string = string.encode('utf-8')
    except UnicodeError:
        pass
    return string


def is_valid_transcription(phono):
    is_valid = True
    valid_cyr_phono = re.compile(to_utf8('^[а-яА-ЯёЁ+-]+$'))
    valid_ascii_phono = re.compile('^[a-zA-Z@_-]+$')
    valid_cyr = valid_cyr_phono.match(phono)
    valid_ascii = valid_ascii_phono.match(phono)
    if not valid_cyr and not valid_ascii:
        is_valid = False
    return is_valid


def word_is_monosyllabic(word):
    vowels_in_word = re.findall(re.compile(to_utf8('[еиюяаоуэыё]')), word)
    if len(vowels_in_word) == 1 and not to_utf8('ё') in word:
        return vowels_in_word[0]
    else:
        return None


def print_feats_list(l):
    ret_str = ''
    for e in l:
        ret_str += e + '/'
    return ret_str[:-1]


def get_g2p_transcription(str_to_transcribe, p):
    result = ''
    if p:
        print >> p.stdin, from_utf8(str_to_transcribe)
        result = p.stdout.readline().strip()
    return result


def get_stress_prediction(word, stress_prediction_model):
    in_pat = re.compile('^[^ ]+\s+[\d.]+\s+(.+)$')
    result = ''
    if stress_prediction_model:
        print >> stress_prediction_model.stdin, from_utf8(word)
        result = stress_prediction_model.stdout.readline().strip()
    m = in_pat.match(result)
    if m:
        result = to_utf8(m.group(1).replace(' ', '').replace('|', '').strip())
    return result


class LexEntries(object):
    def __init__(self):
        super(LexEntries, self).__init__()
        self.lex_entries = {}

    def load_dictionary(self, options_dictionary, log_errors=False):
        self.lex_entries = {}  # reload entries
        errors_found = False
        if log_errors:
            log_file_name = options_dictionary + '.log'
            log_file = open(log_file_name, 'w')
        else:
            log_file_name = ''
            log_file = None
        sys.stdout.write('Loading lexicon: ' + options_dictionary + '\n')
        dictionary_line = re.compile('^([^\s]+)\t([^\s]+)')
        line_num = 0
        for line in open(options_dictionary, 'r'):
            line_num += 1
            line = line.strip()
            if not line.startswith('#'):  # ignore line comments
                m = dictionary_line.match(line)
                if m:
                    ortho = to_utf8(m.group(1))
                    # if there is more than one transcription, just take arbitrarily the first one
                    # this can happen in very few cases (mostly in the so called "hyphen-homographs")
                    phono = to_utf8(m.group(2)).replace(' ', '').split(',')[0]
                    if not is_valid_transcription(phono) and log_errors:
                        log_file.write("[WARNING] transcription not valid in line: " + str(line_num) + '\n')
                        errors_found = True
                    self.lex_entries[ortho] = LexEntry(ortho, phono)
                else:
                    if line:  # ignore empty lines
                        sys.stderr.write('[ERROR] cannot parse line number: ' + str(line_num) + '\n')
        if errors_found and log_errors:
            sys.stderr.write('\nErrors found while reading dictionary file\n')
            sys.stderr.write('Review log file "' + log_file_name + '" and correct the errors\n')
            log_file.close()
            sys.exit(1)
        else:
            if log_errors:
                log_file.close()
                os.unlink(log_file_name)

    def get_transcription(self, ortho, pos_feats=GEN_POS):
        if ortho in self.lex_entries:
            lex_entry = self.lex_entries.get(ortho)
            return lex_entry.get_phono(pos_feats)
        else:
            return ''

    def add_entry(self, ortho, phono, pos_feats):
        self.lex_entries[ortho] = LexEntry(ortho, phono, pos_feats)

    def has_entry(self, ortho):
        if ortho in self.lex_entries:
            return True
        else:
            return False

    def get_entries_num(self):
        return len(self.lex_entries)


class LexEntry(object):
    def __init__(self, ortho, phono, pos_feats=GEN_POS):
        super(LexEntry, self).__init__()
        self.ortho = ortho
        self.pos_feats_phono = {pos_feats: phono}

    def get_phono(self, pos_feats=GEN_POS):
        return self.pos_feats_phono.get(pos_feats)


class HomographEntries(object):
    valid_pos = {"adj": True, "adv": True, "cnj": True, "dee": True,
                 "inj": True, "inv": True, "nn": True, "num": True,
                 "pdv": True, "prn": True, "prp": True, "pt": True,
                 "pth": True, "ptp": True, "vrb": True}

    valid_feats = {"acc": True, "act": True, "adv": True, "anm": True, "cap": True, "cmp": True, "cnj": True,
                   "dat": True, "fem": True, "fin": True, "fst": True, "gen": True, "heu": True, "imp": True,
                   "ind": True, "inf": True, "inj": True, "ins": True, "inv": True, "loc": True, "msc": True,
                   "neu": True, "nom": True, "pdv": True, "pl": True, "prp": True, "prs": True, "pst": True,
                   "psv": True, "pt": True, "pth": True, "sec": True, "sg": True, "sht": True, "trd": True}

    @staticmethod
    def invalid_feat_found(feats):
        invalid_found = False
        for feat in feats:
            if feat and not feat in HomographEntries.valid_feats:
                invalid_found = True
        return invalid_found

    @staticmethod
    def get_phono_from_intersection(target_feats, feats_phono):
        best_phono = ''
        best_intersection = 0
        best_feats = []
        # POS does match and only one entry in homograph list
        if len(feats_phono) == 1:
            best_phono = feats_phono[0][1]
        else:
            for feats, phono in feats_phono:
                intersected = list(set(target_feats) & set(feats))
                if len(intersected) > best_intersection:
                    best_phono = phono
                    best_feats = intersected
                    best_intersection = len(intersected)
        return best_phono, best_feats

    def __init__(self):
        super(HomographEntries, self).__init__()
        self.homograph_entries = {}

    def load_homographs(self, options_homographs, log_errors=False):
        sys.stdout.write('Loading homographs dictionary...\n')
        errors_found = False
        if log_errors:
            log_file_name = options_homographs + '.log'
            log_file = open(log_file_name, 'w')
        else:
            log_file_name = ''
            log_file = None
        dictionary_line1 = re.compile('^(\d+)\s+([^\s]+)\s+([^\(]+)\(([^\)]*)\)\s+\[([^\]]+)\](?:\s+LEX(\d))?$')
        line_num = 0
        for line in open(options_homographs, 'r'):
            line_num += 1
            line = line.strip()
            m1 = dictionary_line1.match(line)
            if m1:
                freq = m1.group(1)
                ortho = to_utf8(m1.group(2))
                pos = m1.group(3).lower()
                feats = m1.group(4).replace(' ', '').split(',')
                raw_phono = to_utf8(m1.group(5))
                # check that the transcription contains valid characters
                for single_phono in raw_phono.replace(' ', '').split(','):
                    if not is_valid_transcription(single_phono) and log_errors:
                        log_file.write("[WARNING] transcription not valid in line: " + str(line_num) + '\n')
                        errors_found = True
                transcriptions = raw_phono.replace(' ', '').split(',')
                # we take the first transcription in the list (transcriptions are ordered by relevance)
                phono = transcriptions[0]
                lex = m1.group(6)
                if not pos in HomographEntries.valid_pos or HomographEntries.invalid_feat_found(feats) and log_errors:
                    log_file.write('invalid tags found in line:\t' + str(line_num) + '\n')
                    errors_found = True
                else:
                    if ortho in self.homograph_entries:
                        homograph_entry = self.homograph_entries.get(ortho)
                        homograph_entry.update_entry(freq, pos, feats, phono, lex)
                        self.homograph_entries[ortho] = homograph_entry
                    else:
                        self.homograph_entries[ortho] = HomographEntry(freq, ortho, pos, feats, phono, lex)
            else:
                if log_errors:
                    log_file.write('error while parsing line:\t' + str(line_num) + '\n')
                    errors_found = True
        if errors_found and log_errors:
            sys.stderr.write('\nErrors found while reading homographs file\n')
            sys.stderr.write('Review log file "' + log_file_name + '" and correct the errors\n')
            log_file.close()
            sys.exit(1)
        else:
            if log_errors:
                log_file.close()
                os.unlink(log_file_name)

    def get_transcription(self, ortho, pos_feats):
        phono = ''
        best_feats = []
        if ortho in self.homograph_entries:
            homograph_entry = self.homograph_entries.get(ortho)
            if pos_feats:
                pos_feats_list = pos_feats.split('/')
                target_pos = pos_feats_list[0]
                target_feats = pos_feats_list[1:]
                idx = 0
                feats_phono = []
                matched_pos = ''
                for pos, feats in homograph_entry.get_pos_feats():
                    if pos == target_pos:
                        feats_phono.append((feats, homograph_entry.get_phono(idx)))
                        matched_pos = pos
                    idx += 1
                if feats_phono:
                    if not homograph_entry.different_transcriptions_found:
                        phono = feats_phono[0][1]
                        best_feats = ['NOT_HOMOGRAPH (getting single transcription)']
                    elif len(feats_phono) == 1:
                        phono = feats_phono[0][1]
                        best_feats = [matched_pos]
                    else:
                        phono, best_feats = HomographEntries.get_phono_from_intersection(target_feats, feats_phono)
            # values in case disambiguation below was not successful
            if not phono:
                phono, best_feats = homograph_entry.get_most_frequent_phono()
        return phono, best_feats


class HomographEntry(object):
    @staticmethod
    def get_highest_freq_idx(freq_list):
        idx = 0
        best_idx = 0
        best_freq = 0
        for freq in freq_list:
            if freq > best_freq:
                best_freq = freq
                best_idx = idx
            idx += 1
        return best_idx

    def __init__(self, freq, ortho, pos, feats, phono, lex):
        super(HomographEntry, self).__init__()
        self.ortho = ortho
        self.freq = []
        self.phono = []
        self.pos_feats = []
        self.lex = []
        self.freq.append(freq)
        self.phono.append(phono)
        self.pos_feats.append((pos, feats))
        self.lex.append(lex)
        # the current version of the homographs list contains entries that have the same transcription for different
        # POS[morpho] tags. These entries are not homographs, in the sense we use this word here, but we have decided
        # to keep them in the list for the time being. The following attribute will be updated when a differing
        # transcription is added to the homograph. This attribute will be checked later for avoiding unnecessary checks
        # and not pollute the output log file
        self.different_transcriptions_found = False

    def update_entry(self, freq, pos, feats, phono, lex):
        self.freq.append(freq)
        if not phono in self.phono:
            self.different_transcriptions_found = True
        self.phono.append(phono)
        self.pos_feats.append((pos, feats))
        self.lex.append(lex)

    def get_pos_feats(self):
        return self.pos_feats

    def get_phono(self, idx):
        return self.phono[idx]

    def get_most_frequent_phono(self):
        if "1" in self.lex:
            return self.phono[self.lex.index("1")], ["LEX1"]
        elif len(self.phono) == 1:
            return self.phono[0], ["SINGLETON"]
        else:
            most_frequent_idx = HomographEntry.get_highest_freq_idx(self.freq)
            return self.phono[most_frequent_idx], ["FREQ"]


sil_punct_symbols = ',;:'
other_punct_symbols = to_utf8('.?"!\'«»')


def tokenize_sentence(sentence, yo_words, tlog):
    russian_input = re.compile(to_utf8('[а-яА-ЯёЁ{0}]+').format(sil_punct_symbols + other_punct_symbols + ' -'))
    m = russian_input.match(sentence)
    if m:
        tokenized_sentence = sentence.lower()
        # delete (to be ignored in the transcription) some of the punctuation symbols
        for sym in other_punct_symbols:
            tokenized_sentence = tokenized_sentence.replace(sym, '')
        # map syntactic hyphen to comma (",") to avoid conflicts with the lexical hyphen
        tokenized_sentence = tokenized_sentence.replace(' - ', ' , ')
        # normalize remaining punctuation symbols (surround them with whitespace)
        tokenized_sentence = re.sub(r'([{0}])'.format(sil_punct_symbols), r' \1 ', tokenized_sentence)
        # normalize whitespace
        tokenized_sentence = re.sub(r'\s+', r' ', tokenized_sentence)
        # find yo words and restore them
        tokenized_sent_with_restored_yo = ''
        word_pos = 0
        for word in tokenized_sentence.split(' '):
            # a word containing 'ё' is supposed to be correctly written. Otherwise, we check if the word could have
            # been written with the letter 'ё' and if yes, we restore then the "correct" spelling
            if (not to_utf8('ё') in word) and \
                    (to_utf8('е') in word) and \
                    yo_words.has_entry(word):
                word = yo_words.get_transcription(word)
                tlog.info('[YOWR]\t%s', from_utf8(word))
            tokenized_sent_with_restored_yo += word + ' '
            word_pos += 1
    else:
        tokenized_sent_with_restored_yo = ''
    return tokenized_sent_with_restored_yo.strip()


def get_pos_prediction(tokenized_sentence):
    pos_predictor_available = False
    original_words = tokenized_sentence.split(' ')
    analyzed_words = []
    pos_predictor_status = 0
    if pos_predictor_available:
        # call external pos predictor passing to it the tokenized sentence, for example:
        # pos_predictor_status, analyzed_words = call_pos_predictor(from_utf8(tokenized_sentence))
        pass
    # in case that no pos prediction was available or it failed, generate a "dummy" prediction
    if not pos_predictor_available or pos_predictor_status > 0:
        for word in original_words:
            # generate SIL for punctuation symbols
            if word in sil_punct_symbols:
                word = SIL
            analyzed_words.append((word, GEN_POS))
    return analyzed_words, pos_predictor_status


def transcribe_line(stress_prediction_process, g2p_process, user_entries, lex_entries, homograph_entries, yo_words,
                    line, tlog=logging.getLogger('nullLogger')):
    error_message = '**ERROR, COULD NOT TRANSCRIBE**'
    line = to_utf8(line).strip()
    line_to_transcribe = ''
    tokenized_sentence = tokenize_sentence(line, yo_words, tlog)
    sentence_transcription = ''
    if tokenized_sentence:
        tlog.info('[NORM]\t%s', from_utf8(tokenized_sentence))
        pos_prediction, pos_predictor_status = get_pos_prediction(tokenized_sentence)
        if pos_predictor_status > 0:
            tlog.info('[INFO]\tPOS analysis failed, ignoring output')
        else:
            word_pos = 0
            # iterate over all words in the input line
            for word, pos_feats in pos_prediction:
                tlog.info('[WORD]\t%s', from_utf8(word))
                if pos_feats:
                    if not pos_feats == GEN_POS:
                        tlog.info('[POSP]\t%s', str(pos_feats))
                else:
                    tlog.info('[POSP]\tNULL')
	  	# generate SIL for punctuation symbols
                if word == SIL:
                    stress_str = SIL
                else:
                    # check whether the word is in the user lexicon
                    stress_str = user_entries.get_transcription(word)
                    if not stress_str:
                        # check if the word is in homographs dictionary
                        stress_str, best_feats = homograph_entries.get_transcription(word, pos_feats)
                        if stress_str:
                            if not 'NOT_HOMOGRAPH' in best_feats[0]:
                                tlog.info('[DISA]\t%s', print_feats_list(best_feats))
                            else:
                                tlog.info('[DISA]\tSINGLETON')
                        else:
                            # check if the word is in simple dictionary
                            stress_str = lex_entries.get_transcription(word)
                            if not stress_str:
                                # not found in any dictionary --> predict stress
                                stress_str = get_stress_prediction(from_utf8(word), stress_prediction_process)
                                # check whether the word is monosyllabic and did not get any stress predicted
                                if not '+' in stress_str:
                                    single_vowel = word_is_monosyllabic(stress_str)
                                    if single_vowel:
                                        stress_str = stress_str.replace(single_vowel, '+' + single_vowel)
                                tlog.info('[INFO]\tstress predicted')
                            else:
                                tlog.info('[INFO]\tentry found in lexicon')
                    else:
                        tlog.info('[INFO]\tentry found in user lexicon')
                tlog.info('[STRS]\t%s', from_utf8(stress_str))
                # correct some possible prediction errors
                stress_str = stress_str.replace(to_utf8('Х'), to_utf8(''))
                # attach POS to the word for G2P purposes (currently only for verbs and adjectives)
                if 'adj' in pos_feats or 'ptp' in pos_feats or 'prn' in pos_feats:
                    stress_str = 'ADJ' + stress_str
                elif 'vrb' in pos_feats:
                    stress_str = 'VERB' + stress_str
                line_to_transcribe += stress_str + ' '
                word_pos += 1
            sentence_transcription = get_g2p_transcription(line_to_transcribe, g2p_process)
            if not sentence_transcription:
                sentence_transcription = error_message
    else:
        sentence_transcription = error_message
    sentence_transcription = re.sub(r'  +', r' ', sentence_transcription.strip())
    return sentence_transcription


def get_number_of_sentences(options_input):
    lines_to_be_processed_num = 0
    for line in open(options_input, 'r'):
        if not line.startswith('#'):
            lines_to_be_processed_num += 1
    return lines_to_be_processed_num


def process_input(options_input, user_entries, lex_entries, homograph_entries, yo_words, stress_prediction_process,
                  g2p_process):
    sys.stdout.write('\n')
    tlog = logging.getLogger('transcription')
    tlog.setLevel(logging.INFO)
    handler = logging.FileHandler(filename=options_input + '.log', mode='w')
    tlog.addHandler(handler)
    out_file = open(options_input + '.g2p', 'w')
    lines_to_be_processed_num = get_number_of_sentences(options_input)
    line_num = 0
    sent_num = 0
    # iterate over all input lines
    for line in open(options_input, 'r'):
        line_num += 1
        line = line.strip()
        if not line.startswith('#'):  # ignore line comments
            sent_num += 1
            sys.stdout.write("\rProcessing sentence: {0}/{1}".format(sent_num, lines_to_be_processed_num))
            tlog.info('[SNUM]\t%d', line_num)
            tlog.info('[SENT]\t%s', line)
            sentence_transcription = transcribe_line(stress_prediction_process, g2p_process, user_entries,
                                                     lex_entries, homograph_entries, yo_words, line, tlog=tlog)
            out_file.write(sentence_transcription + '\n')
            out_file.flush()
            tlog.info('[SPHO]\t%s\n', sentence_transcription)
    sys.stdout.write('\n')
    out_file.close()


class PhonetisaurusInitializationError(Exception):
    def __init__(self):
        sys.stderr.write('[ERROR] could not initialize Phonetisaurus\n')


class TransducerInitializationError(Exception):
    def __init__(self):
        sys.stderr.write('[ERROR] could not initialize G2P transcriber\n')


class ResourcesNotFound(Exception):
    def __init__(self, resources_name):
        sys.stderr.write("[ERROR] path does not exist: '" + resources_name + "'\n")


def get_hash_code(file_name):
    with open(file_name, "rb") as fp:
        contents = fp.read()
    h = hashlib.sha1()
    h.update("blob %s\0%s" % (str(os.stat(file_name).st_size), contents))
    return h.hexdigest()


def initialize_resources(stress_prediction_file, options_g2p_fst, general_lexicon=None, homographs_lexicon=None,
                         user_lexicon=None, yo_list=None):
    dev_null = open(os.devnull, 'wb')
    hash_dict = {}
    options_g2p_fst = options_g2p_fst.replace(' ', '')
    for g2p_fst in options_g2p_fst.split(','):
        if not os.path.exists(g2p_fst):
            raise ResourcesNotFound(g2p_fst)
        else:
            hash_dict[os.path.realpath(g2p_fst)] = get_hash_code(g2p_fst)
    for resources in [stress_prediction_file, general_lexicon, homographs_lexicon, user_lexicon, yo_list]:
        if resources:
            if not os.path.exists(resources):
                raise ResourcesNotFound(resources)
            else:
                if os.path.isdir(resources):
                    for f in os.listdir(resources):
                        f = os.path.join(resources, f)
                        hash_dict[os.path.realpath(f)] = get_hash_code(f)
                else:
                    hash_dict[os.path.realpath(resources)] = get_hash_code(resources)

    # initialize Phonetisaurus process
    try:
        stress_prediction_process = subprocess.Popen(
            ['phonetisaurus-g2p', '--model=' + stress_prediction_file, '--isfile', '--input=/dev/stdin'],
            stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=dev_null)
    except OSError:
        raise PhonetisaurusInitializationError

    # initialize lexica
    user_entries = LexEntries()
    if user_lexicon:
        user_entries.load_dictionary(user_lexicon)
    lex_entries = LexEntries()
    if general_lexicon:
        lex_entries.load_dictionary(general_lexicon)
    yo_words = LexEntries()
    if yo_list:
        yo_words.load_dictionary(yo_list)
    homograph_entries = HomographEntries()
    if homographs_lexicon:
        homograph_entries.load_homographs(homographs_lexicon)

    # initialize transduce process
    try:
        g2p_process = subprocess.Popen(['transduce', '--fst=' + options_g2p_fst], stdout=subprocess.PIPE,
                                       stdin=subprocess.PIPE, stderr=dev_null)
    except OSError:
        raise TransducerInitializationError

    return (stress_prediction_process,
            g2p_process,
            lex_entries,
            homograph_entries,
            user_entries,
            yo_words,
            hash_dict)


def close_resources(stress_prediction_process, g2p_process):
    """
    function to close the subprocesses opened and to remove files that are not needed after exiting from the
    application. Closing the subprocesses is not strictly necessary because they are automatically closed when
    the program that created them exits
    """

    if stress_prediction_process:
        stress_prediction_process.terminate()
    if g2p_process:
        g2p_process.terminate()


def main():
    options_parser = optparse.OptionParser()
    options_parser.add_option('--input', '-i', help='The file containing the words to transcribe')
    options_parser.add_option('--yo_list', '-y', help='List of words that contain the letter <yo> (OPT)')
    options_parser.add_option('--dictionary', '-l', help='A simple dictionary file (OPT)')
    options_parser.add_option('--user', '-u', help='A user lexicon file in the same format as simple dictionary (OPT)')
    options_parser.add_option('--homographs', '-a', help='A file with homographs (OPT)')
    options_parser.add_option('--model_file', '-m', help='Read g2p model from FILE (for stress prediction)')
    options_parser.add_option('--g2p_fst', '-g', help='Path to the G2P FST(s)')

    options, arguments = options_parser.parse_args()
    script_name = os.path.basename(os.path.splitext(inspect.getfile(inspect.currentframe()))[0])

    if options.input and options.model_file and options.g2p_fst:

        if not os.path.exists(options.input):
            sys.stderr.write("[ERROR] path does not exist: '" + options.input + "'\n")
            sys.exit(1)

        sys.stdout.write("\n'" + script_name + "' version " + SCRIPT_VERSION + "\n\n")

        try:
            (stress_prediction_process, g2p_process, lex_entries, homograph_entries, user_entries,
             yo_words, hash_dict) = initialize_resources(options.model_file, options.g2p_fst, options.dictionary,
                                                         options.homographs, options.user, options.yo_list)
            process_input(options.input, user_entries, lex_entries, homograph_entries, yo_words,
                          stress_prediction_process, g2p_process)
            close_resources(stress_prediction_process, g2p_process)
        except (PhonetisaurusInitializationError, TransducerInitializationError, ResourcesNotFound):
            sys.exit(1)

    else:
        options_parser.print_help()
        sys.stdout.write("\n'" + script_name + "' version " + SCRIPT_VERSION + "\n\n")

# call the main() function to start the program.
if __name__ == '__main__':
    main()
