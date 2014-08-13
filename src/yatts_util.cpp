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
 * yatts_util.cpp
 */



#include "yatts_util.h"
#include <cstring>
#include <algorithm>

int to_uint(char const *s) {
    int result = 0;
    if (!*s) {
        throw std::invalid_argument("invalid input string");
    }
    while (*s) {
        if (*s >= '0' && *s <= '9') {
            result = result * 10 + (*s - '0');
        } else {
            throw std::invalid_argument("invalid input string");
        }
        s++;
    }
    return result;
}


std::vector<std::string> tokenize_utf8_string(std::string* utf8_string, std::string* delimiters,
                                    int limit) {
    /*
     Support for tokenizing a utf-8 string. Adapted to also support delimiters and a limit.
     Note that (unlike Joe's version) any of the utf8 characters in delimiters is a delimiter (like strtok),
     not the whole string.
     Note that leading, trailing or multiple consecutive delimiters will result in
     empty vector elements.  Normally should not be a problem but just in case.
     Also note that any tokens that cannot be found in the model symbol table will be
     deleted from the input word prior to grapheme-to-phoneme conversion.

     http://stackoverflow.com/questions/2852895/c-iterate-or-split-utf-8-string-into-array-of-symbols#2856241

     schsafra: adapted from http://code.google.com/p/phonetisaurus/ (phonetisaurus-0.7.8) by Josef Robert Novak

     */
    char* str = (char*) utf8_string->c_str(); // utf-8 string
    char* str_i = str;                         // string iterator
    char* str_j = str;
    char* end = str + strlen(str) + 1;           // end iterator
    std::vector<std::string> string_vec;
    std::vector<int> delim_code;
    if (delimiters->compare("") != 0) {
        string_vec.push_back("");
        char* delim_i = (char*) delimiters->c_str();
        char* delim_end = delim_i + strlen(delim_i) + 1;
        do {
            delim_code.push_back(utf8::next(delim_i, delim_end));
        } while (delim_i < delim_end);
    }
    do {
        str_j = str_i;
        utf8::uint32_t code = utf8::next(str_i, end); // get 32 bit code of a utf-8 symbol
        if (code == 0) {
            continue;
        }
        int start = strlen(str) - strlen(str_j);
        int end = strlen(str) - strlen(str_i);
        int len = end - start;

        if (delimiters->compare("") == 0) {
            string_vec.push_back(utf8_string->substr(start, len));
        } else {
            if ((limit == 0 || string_vec.size() < limit) &&
                    std::find(delim_code.begin(), delim_code.end(), code) != delim_code.end()) {
                string_vec.push_back("");
            } else {
                string_vec[string_vec.size() - 1] += utf8_string->substr(start,
                                                                         len);
            }
        }
    } while (str_i < end);

    return string_vec;
}


/*
 * http://stackoverflow.com/questions/9620437/string-const-char-size-t-to-int
 */
int to_int(char const *s, size_t count)
{
     size_t i = 0 ;
     if ( s[0] == '+' || s[0] == '-' )
          ++i;
     int result = 0;
     while(i < count)
     {
          if ( s[i] >= '0' && s[i] <= '9' )
          {
              result = result * 10  - (s[i] - '0');  //assume negative number
          }
          else
              throw std::invalid_argument("invalid input string");
          i++;
     }
     return s[0] == '-' ? result : -result; //-result is positive!
}
