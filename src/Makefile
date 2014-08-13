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
# Author : Schamai Safra
#
#
# Makefile



TARGETS=transduce

### transduce: stand-alone transducer tool (UTF8 characters as input labels)
OBJS_transduce=transduce.o yatts_util.o Utf8Transducer.o
LIB_transduce = fst dl m rt

LIBS=../libs  /usr/local/lib

TARGET_LIBS = ${LIB_${1}:%=-l%}
TARGET_OBJS = ${OBJS_${1}:%=%}
OBJS=${foreach target,${TARGETS:%=OBJS_%},${${target}}}

########################################################################
# Macro definitions for "standard" C and C++ compilations
#
CPPFLAGS= -g3 -O0   -I../include -I./3rdparty -I/usr/include -fPIC
#
CFLAGS=-g
#
LINK=g++ $(CPPFLAGS)

LFLAGS=$(LIBS:%=-L%)
#
.SUFFIXES:
.SUFFIXES: .d .o .h .c .cc .C .cpp
.c.o: ; $(CC) $(CFLAGS) -MMD -c $*.c
.cc.o: ; $(CPP) $(CPPFLAGS) -MMD -c $*.cc
.C.o: ; $(CPP) $(CPPFLAGS) -MMD -c $*.C
.cpp.o: ; $(CPP) $(CPPFLAGS) -MMD -c $*.cpp

CC=gcc
CPP=g++

%.d: %.c
	touch $@
%.d: %.cc
	touch $@
%.d: %.C
	touch $@
%.d: %.cpp
	touch $@

DEPENDENCIES = $(OBJS:.o=.d)

#
# Targets:
#
all: $(TARGETS:%=./build/%)

.SECONDEXPANSION:
./build/%: $$(OBJS_%)
	echo dependencies $^
	$(LINK) $(FLAGS) -o $@ $^ $(LFLAGS) $(call TARGET_LIBS,$*)

cleantargets:
	-rm -f $(TARGETS:%=../build/%) $(OBJS)

clean: cleantargets
	-rm -f $(DEPENDENCIES)

### Makefile ends here

