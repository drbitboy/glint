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
