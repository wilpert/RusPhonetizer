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
 * Utf8Transducer.cpp
 */



#include "utf8ext.h"
#include "Utf8Transducer.h"

namespace yatts {

Utf8Transducer::Utf8Transducer(): symbolTable(0) {
    message[0] = 0;
    // TODO Auto-generated constructor stub

}

Utf8Transducer::~Utf8Transducer() {
    // TODO Auto-generated destructor stub
}

Utf8Transducer::Status Utf8Transducer::appendFst(VectorFst<StdArc>*& transducer, string id) {
    if (id == "") {
        char buf[10];
        snprintf(buf, 10, "%lu",transducers.size());
        id = string(buf);
    }
    if (transducer) {
        transducers.push_back(transducer);
        transducer_ids.push_back(id);
        return OK;
    } else {
        snprintf(message, maxMsgLength, "Cannot append null FST '%s'", id.c_str());
        return WARN;
    }
}

Utf8Transducer::Status Utf8Transducer::appendFst(const string& file_name, string id) {
    if (id == "") {
        char buf[10];
        snprintf(buf, 10, "%lu",transducers.size());
        id = string(buf);
    }
    VectorFst<StdArc> * fst = 0;
    try {
         fst = VectorFst<StdArc>::Read(file_name);
    } catch (exception& e) {
        snprintf(message, maxMsgLength, "Cannot load FST '%s' from file '%s': %s", id.c_str(), file_name.c_str(),e.what());
        return WARN;
    }
    if (!fst) {
        snprintf(message, maxMsgLength, "Cannot load FST '%s' from file '%s'", id.c_str(), file_name.c_str());
        return WARN;
    }
    // sort arcs by input label
    ArcSort(fst, ILabelCompare<StdArc>());
    // ------- Delete input symbols (assume utf8 input)
    fst->SetInputSymbols(NULL);
    this->appendFst(fst, id);
    return OK;
}

Utf8Transducer::Status Utf8Transducer::transduceText(string text, string& result) {
    string::iterator readPos = text.begin();
    utf8::uint32_t codePoint;
    vector<StdArc::Label> input;
    //string utf8line;
    while (readPos < text.end()) {
        codePoint = utf8::next_skip_invalid(readPos, text.end());
        input.push_back(codePoint);
    }
    try {
        bool ok = true;
        VectorFst<StdArc> * fst = MakeInputFST<StdArc>(input), * fst2;
        for (size_t i = 0; i < transducers.size(); i++) {
            fst2 = new VectorFst<StdArc>(
                    ComposeFst<StdArc>(*fst, *transducers[i]));
            delete fst;
            fst = fst2;
            Connect(fst);
            if (fst->NumStates() == 0) {
                snprintf(message, maxMsgLength, "No transduction after applying transducer '%s'", transducer_ids[i].c_str());
                break;
            }
        }
        if (fst && fst->Start() >= 0 && fst->NumArcs(fst->Start()) > 0) {
            fst::VectorFst<StdArc> nbest_paths;
            fst::ShortestPath(*fst, &nbest_paths, 2);
            delete fst;
            vector<unsigned short> utf16line;
            StdArc::StateId cur_state = nbest_paths.Start();
            if (cur_state < 0 || nbest_paths.NumArcs(cur_state) < 1) {
                ok = false;
            } else {
                if (nbest_paths.NumArcs(cur_state) != 1) {
                    snprintf(message, maxMsgLength,
                            "ambiguous transduction (%s)", text.c_str());
                }
                for (;
                        nbest_paths.Final(cur_state)
                                == StdArc::Weight::Zero();) {
                    fst::ArcIterator<fst::Fst<StdArc> > aiter(nbest_paths,
                            cur_state);
                    StdArc arc = aiter.Value();
                    if (arc.olabel != 0) {
                        utf16line.push_back(arc.olabel);
                    }
                    cur_state = arc.nextstate;
                }
                utf8::utf16to8(utf16line.begin(), utf16line.end(),
                        back_inserter(result));
            }
        } else {
            ok = false;
        }
        if (ok) {
            return OK;
        } else {
            //that's a temporary hack for Alexis' script to work. It is wrong because an empty
            //result line could also be a valid transduction
           return WARN;
        }
    } catch (std::exception& e) {
        cerr << e.what() << endl;
        throw;
    }
}


Utf8Transducer::Status Utf8Transducer::readOrNewSymtab(string file, string name) {
    if (!file.empty()) {
        ifstream st_fp;
        st_fp.open(file.c_str());
        if (st_fp.is_open()) {
            symbolTable = SymbolTable::ReadText(st_fp,name);
        }
        st_fp.close();
    } else {
        symbolTable = new SymbolTable("name");
    }
    if (!symbolTable) {
        snprintf(message, maxMsgLength, "Couldn't read symbol table %s from file %s\n", name.c_str(), file.c_str());
        return WARN;
    }
    return OK;
}


const char* Utf8Transducer::getMessage() const {
    return message;
}

} /* namespace yatts */
