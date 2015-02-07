
### Assume cspice is symlink pointing to SPICE subdirectory

SPICETOP=cspice

SPICEINC=$(SPICETOP)/include
SPICELIB=$(SPICETOP)/lib

CPPFLAGS=-I$(SPICEINC)
LDLIBS=$(SPICELIB)/cspice.a -lm


default: glint
