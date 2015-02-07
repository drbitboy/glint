# glint
Calculate glint angle for TOMS/EP satellite using PySPICE


Usage:

    Full-up script to create updated TOMS/EP HDF5 files:


        find TOMSEPL2/1996/07/ -name '*.he5' | grep  '_glint\.he5$' | sort | xargs python tag.py


    Prototype:

        python glint.py < glint.py



Uses NAIF/SPICE (PySPICE), h5py

Also needs two SPICE kernels:

    http://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0011.tls
  
    http://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00010.tpc

    http://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de432s.bsp

    - provided
