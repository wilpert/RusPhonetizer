### Makefile --- 

## Author:
## Keywords: 
## X-URL: 

TARGETS=../libs/libjson.a
OBJS=json/json.o


########################################################################
# Macro definitions for "standard" C and C++ compilations
## 
#CPPFLAGS=-g3 -O0 -fprofile-arcs -ftest-coverage -Ijson -fPIC
CPPFLAGS=-g3 -O0   -Ijson -fPIC
#
CFLAGS=-g
# 
#  What is the name of the program you want to create?  (See below for notes
#     on using this makefile to generate multiple programs.)
#
LINK=g++ $(CPPFLAGS)
#LINK=gcc $(CFLAGS)
# 
#  Define special linkage flags.  Usually, these are used to include
#  special libraries of code, e.g., -lm to add the library of mathematical
#  routines such as sqrt, sin, cos, etc.
LFLAGS=-lm
#
#
#
#  In most cases, you should not change anything below this line.
#
#  The following is "boilerplate" to set up the standard compilation
#  commands:
#
.SUFFIXES:
.SUFFIXES: .d .o .h .c .cc .C .cpp
.c.o: ; $(CC) $(CFLAGS) -MMD -c $*.c
.cc.o: ; $(CPP) $(CPPFLAGS) -MMD -c $*.cc 
.C.o: ; $(CPP) $(CPPFLAGS) -MMD -c $*.C
.cpp.o: ; $(CPP) $(CPPFLAGS) -MMD -c $*.cpp -o $@

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
all: $(TARGETS)

clean:
	-rm -f $(TARGETS) $(DEPENDENCIES) $(OBJS) make.dep

../libs/libjson.a: json/json.o
	ar rcs $@ $^

make.dep: $(DEPENDENCIES)
	-cat $(DEPENDENCIES) > make.dep

include make.dep

### Makefile ends here
