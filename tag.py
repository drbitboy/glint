"""
tag.py - TOMS Add Glint script

Add glint angle to TOMS (Total Ozone Mapping Spectrometer) HDF5 files

Usage:

  find TOMSEPL2/1996/07/ -name '*.he5' | grep  '_glint\.he5$' | sort | xargs python tag.py

Dependencies:

  h5py; numpy; PySPICE; PDSImage; listfauxfile

  - the latter two are provided in this repository

"""

import sys
import h5py
import spice
import numpy
import PDSImage
import listfauxfile


if __name__=="__main__" and sys.argv[1:]:

  ### Conversion from radans to degrees and back
  rpd,dpr = spice.rpd(),spice.dpr()

  ### Load this python script as a SPICE kernel
  spice.furnsh(__file__)

  """
Meta-kernel:

  The files lister here must exist at the location specified

\begindata
KERNELS_TO_LOAD = (
  'naif0011.tls'
  'pck00010.tpc'
  'de432s.bsp'
)
\begintext
"""

  ### Earth equatorial and polar radii; calculate flattening
  re = spice.gdpool('BODY399_RADII',0,1)[1]
  rp = spice.gdpool('BODY399_RADII',2,1)[1]
  flattening = (re-rp) / re

  ######################################################################
  def glintangle(scAltKm,scLonDeg,scLatDeg,surfLonDeg,surfLatDeg,uvEarth2Sun):
    """Function to calculate glint angle

       Inputs:
         S/C altitude, Longitude, Latitude
         Surface point Longitude, Latitude (altitude is zero by definition)
         Ephemeris time, s past J2000 EPOCH
    """

    toms_alt_km = scAltKm
    toms_lon_rad = rpd * scLonDeg           ### Scale degrees to radians
    toms_lat_rad = rpd * scLatDeg           ### Scale degrees to radians

    surf_lon_rad = rpd * surfLonDeg
    surf_lat_rad = rpd * surfLatDeg

    ### Convert TOMS and surface points geodetic positions to ECEF vectors
    toms_vec = spice.georec(toms_lon_rad,toms_lat_rad,toms_alt_km,re,flattening)
    surfPoint = spice.georec(surf_lon_rad,surf_lat_rad,0.,re,flattening)

    ### Get normal at surface point, ECEF unit vector
    uvSurfNormal = spice.surfnm(re,re,rp,surfPoint)

    ### Get cosine of incidence angle (angle between Sun & surface normal vector)
    mu = spice.vdot(uvEarth2Sun,uvSurfNormal)

    if mu <= 0.: return 999.9

    uvReflect = spice.vsub(spice.vscl(2.*mu,uvSurfNormal),uvEarth2Sun)  ### Get specular reflection vector

    ### Return glint angle
    return dpr * spice.vsep(uvReflect,spice.vsub(toms_vec,surfPoint))

  ### End of glint angle calculation
  ######################################################################


  ######################################################################
  for fnInput in (__name__=="__main__" and sys.argv[1:] or []):

    if fnInput[-4:] != '.he5':
      sys.stderr.write("### Skipping file '%s'; does not end in '.he5'\n" % (fnInput,))
      continue

    if fnInput[-10:] == '_glint.he5':
      sys.stderr.write("### Skipping file '%s'; ends in '_glint.he5'\n" % (fnInput,))
      continue

    ### Build output filename

    fnToks = fnInput.split('.')
    fnToks[-2] += '_glint'
    fnOutput = '.'.join(fnToks)

    try:
      fOutput = h5py.File(fnOutput,'w-')
    except:
      sys.stderr.write("### Skipping creation of glint file '%s'; it already exists or is otherwise un-writeable\n" % (fnOutput,))
      continue

    ### Read HDF5 file
    fInput=h5py.File(fnInput,'r')

    ### Get the inputs from the input HDF5 file
    getThem = lambda s: numpy.array(fInput[s])

    tomsOffsetTimes,surfLatDegs,surfLonDegs,scAltKms,scLatDegs,scLonDegs = map(getThem
, [s.strip() for s in """
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/Time
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/Latitude
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/Longitude
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/SpacecraftAltitude
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/SpacecraftLatitude
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/SpacecraftLongitude
""".strip().split('\n')]
)

    ### Convert .../CoreMetadata to string, parse as ODL using PDSImage.py
    faux=listfauxfile.FILE(numpy.array(fInput['HDFEOS INFORMATION/CoreMetadata']).tostring().replace('\0',''))
    pdsi=PDSImage.PDSImage()

    ### dcmd ocontains recursive dictionaries
    dcmd=pdsi._downone(faux)

    ### Extract start time from dcmd (CoreMetadata) as ISO UTC string
    firstTomsUTC = '%sT%s' % (dcmd['INVENTORYMETADATA']['RANGEDATETIME']['RANGEBEGINNINGDATE']['VALUE']
                             ,dcmd['INVENTORYMETADATA']['RANGEDATETIME']['RANGEBEGINNINGTIME']['VALUE']
                             ,)

    ### Combine start time and /Time offset to get the TOMS data zero epoch as seconds past J2000 epoch
    ### N.B. is typically (always?) equivalent to 1993-01-01T00:00:00 UTC
    tomsZeroEpoch = spice.utc2et(firstTomsUTC) - tomsOffsetTimes[0]

    print('%s(Epoch)  %s(Start)  %s' % (spice.et2utc(tomsZeroEpoch,'ISOC',1),firstTomsUTC,fnInput,))

    ### Iterators
    twoDshape = surfLonDegs.shape
    rowIter,pixelIter = map(xrange,twoDshape)

    glintAngles = numpy.zeros(twoDshape,dtype=numpy.float32)

    for row in rowIter:

      ### Earth-Sun vector, convert to unit vector
      earth2Sun = spice.spkezr('SUN',tomsZeroEpoch+tomsOffsetTimes[row],'IAU_EARTH','LT+S','EARTH')[0][:3]
      uvEarth2Sun = spice.vhat(earth2Sun)

      scAltKm = scAltKms[row]
      scLonDeg = scLonDegs[row]
      scLatDeg = scLatDegs[row]

      for pixel in pixelIter:
        glintAngles[row,pixel] = glintangle(scAltKm
                                           ,scLonDeg
                                           ,scLatDeg
                                           ,surfLonDegs[row,pixel]
                                           ,surfLatDegs[row,pixel]
                                           ,uvEarth2Sun
                                           )

    ### Get top level groups for copying
    topGroups = []
    def addtopgroup(name):
      if name.find('/')==-1: topGroups.append(name)

    fInput.visit(addtopgroup)

    for topGroup in topGroups: fOutput.copy( fInput[topGroup], topGroup)

    fInput.close()

    fOutput.create_dataset('HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/GlintAngle',data=glintAngles)

    fOutput.close()

"""
HDFEOS
HDFEOS/ADDITIONAL
HDFEOS/ADDITIONAL/FILE_ATTRIBUTES
HDFEOS/SWATHS
HDFEOS/SWATHS/EP TOMS Column Amount O3
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/APrioriLayerO3
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/AlgorithmFlags
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/CloudFraction
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/CloudTopPressure
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/ColumnAmountO3
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/LayerEfficiency
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/MeasurementQualityFlags
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/NValue
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/O3BelowCloud
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/QualityFlags
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/Reflectivity331
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/Reflectivity360
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/Residual
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/ResidualStep1
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/ResidualStep2
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/SO2index
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/Sensitivity
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/StepOneO3
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/StepTwoO3
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/TerrainPressure
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/UVAerosolIndex
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/Wavelength
HDFEOS/SWATHS/EP TOMS Column Amount O3/Data Fields/dN_dR
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/GroundPixelQualityFlags
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/Latitude
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/Longitude
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/RelativeAzimuthAngle
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/SecondsInDay
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/SolarAzimuthAngle
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/SolarZenithAngle
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/SpacecraftAltitude
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/SpacecraftLatitude
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/SpacecraftLongitude
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/TerrainHeight
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/Time
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/ViewingAzimuthAngle
HDFEOS/SWATHS/EP TOMS Column Amount O3/Geolocation Fields/ViewingZenithAngle
HDFEOS INFORMATION
HDFEOS INFORMATION/ArchivedMetadata
HDFEOS INFORMATION/CoreMetadata
HDFEOS INFORMATION/StructMetadata.0
"""
