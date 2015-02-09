
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


default: glint glint_f

glint_f: glint_f.f
	$(LINK.f) $^ $(FLIBS) -o $@

