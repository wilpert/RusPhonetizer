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
 * utf8ext.h
 */



#ifndef UTF8EXT_H_
#define UTF8EXT_H_

#include "utf8/utf8.h"
#include <stdexcept>

namespace utf8 {

using namespace std;
template <typename T, size_t N>
T* begin(T(&arr)[N]) { return &arr[0]; }
template <typename T, size_t N>
T* end(T(&arr)[N]) { return &arr[0]+N; }

template <typename T, size_t N>
bool is_in(T x, const T(&arr)[N]) {
    const T* lb = lower_bound(begin(arr), end(arr), x);
    return (end(arr) != lb) && (*lb == x);
}


const uint32_t WHITESPACE_CHARS[] = {32, 160, 5760, 6158, 8192, 8193, 8194, 8195,8196, 8197, 8198, 8199, 8200, 8201, 8202, 8203, 8204,  8205, 8239, 8287, 8288, 12288, 65279};

const uint32_t CR = 13, LF = 10;
const uint32_t EOL_CHARS[] = {10, 11, 12, 13, 133, 8232, 8233};

// CR=13, LF=10, 11, 12, 133, 8232, 8233


inline bool is_whitespace(uint32_t cp) {
        return is_in(cp, WHITESPACE_CHARS);
}

inline bool is_EOL(uint32_t cp) {
        return is_in(cp, EOL_CHARS);
}


/**
 * like utf8::next, but in case of invalid sequence,
 * consumes irreparable octets before throwing.
 * @param start
 * @param end
 * @return next code point, if valid
 */
template <typename octet_iterator>
uint32_t next_skip_invalid(octet_iterator& it, octet_iterator end)
{
    uint32_t cp = 0;
    internal::utf_error err_code = utf8::internal::validate_next(it, end, cp);
    octet_iterator bad;
    switch (err_code) {
        case internal::UTF8_OK :
            break;
        case internal::NOT_ENOUGH_ROOM :
            throw not_enough_room();
            break;
        case internal::INVALID_LEAD :
            bad = it;
            it++;
            throw invalid_utf8(*bad);
            break;
        case internal::INCOMPLETE_SEQUENCE :
        case internal::OVERLONG_SEQUENCE :
            bad = it;
            it++;
            while (it != end && utf8::internal::is_trail(*it))
                ++it;
            throw invalid_utf8(*bad);
            break;
        case internal::INVALID_CODE_POINT :
            it++;
            while (it != end && utf8::internal::is_trail(*it))
                ++it;
            throw invalid_code_point(cp);
    }
    return cp;
}


}


#endif /* UTF8EXT_H_ */
