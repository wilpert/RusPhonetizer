/* Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Copyright 2014 Yandex LLC
 * All Rights Reserved.
 *
 * Author : Schamai Safra
 *
 *
 * transduce.cpp
 */



#include <float.h>
#include <stdexcept>
#include <fst/fstlib.h>
#include <fst/script/print.h>
#include <fst/dfs-visit.h>
#include <fst/arc-map.h>
#include <fst/extensions/far/far.h>
#include <fst/extensions/far/farscript.h>
#include <utf8/utf8.h>
#include "utf8ext.h"
#include "yatts_util.h"
#include "Utf8Transducer.h"

using namespace fst;
using namespace yatts;

#define VERBOSE 1
#if VERBOSE
#define msg(x, ...) fprintf(stderr, x, ##__VA_ARGS__);
#else
#define msg(x, ...)
#endif
#define SAVE_INTERMEDIATE 0

DEFINE_string(fst, "", "rewrite FST.");
DEFINE_string( symbols, "", "symbol table of the rewrite FST.");



void ProcessCorpus(string corpus_filename, Utf8Transducer& transducer, FILE * fp) {
    istream * ifp = &cin;
    ifstream corpus_fp;
    if (corpus_filename != "-") {
        corpus_fp.open(corpus_filename.c_str());
        if (corpus_fp.is_open()) {
            ifp = &corpus_fp;
        } else {
            msg("*** warning: Can't open '%s' for reading.\n",
                    corpus_filename.c_str());
            exit(1);
        }
    }
    string line;
    int lineCount = 0;
    while (ifp->good()) {
        getline(*ifp, line);
        if (line.compare("") == 0) {
            continue;
        }
        lineCount++;
        try {
            string utf8line;
            int status = transducer.transduceText(line, utf8line);
            switch (status) {
                case Utf8Transducer::OK:
                    fprintf(fp, "%s\n", utf8line.c_str());
                    break;
                case Utf8Transducer::WARN:
                    msg("*** warning: %s\n", transducer.getMessage());
                    fprintf(fp, "%s\n", utf8line.c_str());
                    break;
                default:
                    msg("*** warning: %s\n", transducer.getMessage());
                    fprintf(fp, "\n");
                    break;
            }

        } catch (std::exception& e) {
            cerr << e.what() << endl;
            throw;
        }
    }
    corpus_fp.close();
}



int main(int argc, char **argv) {
    string usage =
            "Transduce (rewrite) words according to rewrite-fst .\n\n  Usage: ";
    usage += argv[0];
    usage += " [input.utf [output.utf]]\n";
    set_new_handler(FailedNewHandler);
    SetFlags(usage.c_str(), &argc, &argv, true);

#define MANDATORY(name)                        \
    if (FLAGS_ ## name == "") {                \
        fprintf(stderr,"*** Error: --" # name " is mandatory\n");   \
        exit(1);                               \
    }

    MANDATORY(fst);

    if (argc > 3) {
        ShowUsage();
        return 1;
    }

    string in_name = (argc > 1 && (strcmp(argv[1], "-") != 0)) ? argv[1] : "-";
    string out_name = argc > 2 ? argv[2] : "-";

    yatts::Utf8Transducer transducer;

    // currently not used: transducer deletes symbol tables when reading fsts
    // later we may use one, or even read one for each fst
    transducer.readOrNewSymtab(FLAGS_symbols, "symbol_table");

    string delim = string(",");

    vector<string> rules = tokenize_utf8_string(&FLAGS_fst, &delim);
    for (int i = 0; i < rules.size(); i++) {
        Utf8Transducer::Status s = transducer.appendFst(rules[i], rules[i]);
        switch (s) {
        case Utf8Transducer::OK:
            msg("loaded fst '%s'\n", rules[i].c_str());
            break;
        case Utf8Transducer::WARN:
            msg("*** warning: %s\n", transducer.getMessage());
            break;
        case Utf8Transducer::ERROR:
            throw runtime_error(transducer.getMessage());
        default:
            msg("*** warning: %s\n", transducer.getMessage());
            break;
        }
    }

    FILE * fp;
    if (out_name == "-") {
        fp = stdout;
    } else {
        fp = fopen(out_name.c_str(), "w");
    }
    ProcessCorpus(in_name, transducer, fp);
}
