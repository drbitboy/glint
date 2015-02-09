
### Assume cspice is symlink pointing to SPICE subdirectory

SPICETOP=cspice
TOOLKITTOP=toolkit

SPICEINC=$(SPICETOP)/include
SPICELIB=$(SPICETOP)/lib

TOOLKITINC=$(TOOLKITTOP)/include
TOOLKITLIB=$(TOOLKITTOP)/lib

CPPFLAGS=-I$(SPICEINC)
LDLIBS=$(SPICELIB)/cspice.a -lm

FLIBS=$(TOOLKITLIB)/spicelib.a


EXES=glint_c glint_f

all: $(EXES)

test: all
	for exe in $(EXES) ; do ./$$exe > $${exe#glint_}.out ; done
	sum c.out f.out
	diff c.out f.out -yW200 --suppress-c

glint_f: glint_f.f
	$(LINK.f) $^ $(FLIBS) -o $@

clean:
	$(RM) $(EXES) c.out f.out *.pyc
