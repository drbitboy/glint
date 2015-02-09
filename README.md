# glint
Calculate glint angle for TOMS/EP satellite using PySPICE


Usage:

    Full-up script to create updated TOMS/EP HDF5 files:


        find TOMSEPL2/1996/07/ -name '*.he5' | grep -v '_glint\.he5$' | sort | xargs python tag.py


    Prototype:

        python glint.py < glint.py



Uses NAIF/SPICE (PySPICE), h5py

Also needs two SPICE kernels:

    http://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0011.tls
  
    http://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00010.tpc

    http://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de432s.bsp

    - provided

Data source (HDF5 format files of TOMS/EP data):

  http://mirador.gsfc.nasa.gov/cgi-bin/mirador/presentNavigation.pl?tree=project&project=TOMS

also

  ftp://acdisc.gsfc.nasa.gov/data/s4pa/Earth_Probe_TOMS_Level2/TOMSEPL2/


Manifest
========


    tag.py - Input TOMS/EP .he5 HDF5 files, calculate and append glint angle, write _glint.he5

    glint_c.c - C version testing getelm_c/ev2lin_
    glint_f.f - FORTRAN version  testing getelm/ev2lin

    glint.py - prototype for tag.py

    listfauxfile.py - support modules for tag.py
    PDSImage.py     - support module for tag.py

    Makefile - build glint_c and glint_f

    README.md - this file

tomsnew.he5

SPICE Kernels
-------------

    de432s.bsp
    naif0011.tls
    pck00010.tpc


Other useful files/links/directories
====================================

    TOMSEPL2/ - TOMS/EP .he5 files e.g.

        wget --mirror -nv -np -nH --cut-dirs=3  ftp://acdisc.gsfc.nasa.gov/data/s4pa/Earth_Probe_TOMS_Level2/TOMSEPL2/

    cspice   - Symlink for building glint_c.c
    toolkit  - Symlink for building glint_f.f

    e.g.

        lrwxrwxrwx  1 carcich carcich       20 Feb  6 14:13 cspice -> /home/carcich/cspice
        lrwxrwxrwx  1 carcich carcich       21 Feb  9 14:26 toolkit -> /home/carcich/toolkit
