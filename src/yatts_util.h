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
 * yatts_util.h
 */



#include <utf8/utf8.h>
#include <vector>
#include <string>

#ifndef YATTS_UTIL_H_
#define YATTS_UTIL_H_

int to_uint(char const *s);

std::vector<std::string> tokenize_utf8_string( std::string* utf8_string, std::string* delimiter, int limit = 0 );

template <class T, class A>
T join(const A &begin, const A &end, const T &t)
{
  T result;
  A it = begin;
  if (it != end) {
   result.append(*it++);
  }
  for( ; it!=end; ++it) {
   result.append(t).append(*it);
  }
  return result;
}


#endif /* YATTS_UTIL_H_ */
