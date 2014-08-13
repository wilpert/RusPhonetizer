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
 * Utf8Transducer.h
 */



#ifndef UTF8TRANSDUCER_H_
#define UTF8TRANSDUCER_H_
#include <utf8/utf8.h>
#include <fst/fstlib.h>

namespace yatts {

using namespace fst;

static const int maxMsgLength = 1000;

class Utf8Transducer {
public:
    enum Status {
        OK,
        WARN,
        ERROR,
    };
    Utf8Transducer();
    virtual ~Utf8Transducer();
    Status appendFst(VectorFst<StdArc>*& transducer, string id = string(""));
    Status appendFst(const string& file_name, string id = string(""));
    Status transduceText(string text, string& result);
    Status readOrNewSymtab(string file, string name);
    const char* getMessage() const;

protected:
    template <class Arc>
    VectorFst<Arc> * MakeInputFST(vector<typename Arc::Label> input);
    vector<VectorFst<StdArc>*> transducers;
    SymbolTable * symbolTable;
    vector<string> transducer_ids;
    char message[maxMsgLength];
};

template <class Arc>
VectorFst<Arc> * Utf8Transducer::MakeInputFST(vector<typename Arc::Label> input) {
    typedef typename Arc::StateId StateId;
    typedef typename Arc::Weight Weight;
    typedef typename Arc::Label Label;
    fst::VectorFst<Arc> * ifst = new fst::VectorFst<Arc>();
    ifst->DeleteStates();
    StateId s = ifst->AddState(), nextstate = fst::kNoStateId;
    ifst->SetStart(s);
    for (size_t i = 0; i < input.size(); i++) {
        nextstate = ifst->AddState();
        Arc arc(input[i], input[i], Weight::One(), nextstate);
        ifst->AddArc(s, arc);
        s = nextstate;
    }
    ifst->SetFinal(s, Weight::One());
    return ifst;
}


} /* namespace yatts */


#endif /* UTF8TRANSDUCER_H_ */
