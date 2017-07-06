# Compiler
CC=gcc

# Code and build directories
BINDIR=./
BUILDDIR=build
SRCDIR=src
INCDIR=include
LIBDIR=lib
EXEC=$(BINDIR)/hist


# Sources, libraries and object locations
SRC := $(shell find $(SRCDIR) -name *.cpp -or -name *.c)
OBJ := $(patsubst $(SRCDIR)/%.cpp,$(BUILDDIR)/%.o,$(SRC))

LDFLAGS=-levent -lopenslide

# Include directory
INCFLAGS := $(addprefix -I,$(INCDIR))
CFLAGS = $(INCFLAGS) -Wall -Wextra -g -O0

all: $(EXEC)

$(EXEC): $(OBJ)
	$(CC) $(OBJ) -o $@ $(LDFLAGS)

$(BUILDDIR)/%.o: $(SRCDIR)/%.cpp
	$(CC) $(CFLAGS) -c $< -o $@


.PHONY: clean

clean:
	rm -f hist build/* include/*.gch


