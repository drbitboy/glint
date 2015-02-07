import sys
import spice

rpd,dpr = spice.rpd(),spice.dpr()

if __name__=="__main__":

  spice.furnsh(__file__)

  ### Earth equatorial and polar radii calculate flattening
  re = spice.gdpool('BODY399_RADII',0,1)[1]
  rp = spice.gdpool('BODY399_RADII',2,1)[1]
  f = (re-rp) / re

  for line in sys.stdin:

    ### Read one line of input at a time; only use lines that start with data:
    if line[:5]!="data:": continue

    linestrip = line[5:].strip()

    linetoks = linestrip.split()   ### Break line into tokens

    toms_alt_m,toms_lon_deg,toms_lat_deg,sX,sY,sZ,surf_lon_deg,surf_lat_deg = map(float,linetoks[:-1])
    utc = linetoks[-1]

    uvEarth2Sun = spice.vhat((sX,sY,sZ,))   ### Ensure Sun vector is unit length

    toms_alt_km = 1e-3 * toms_alt_m         ### Scale altitude to km
    toms_lon_rad = rpd * toms_lon_deg       ### Scale degrees to radians
    toms_lat_rad = rpd * toms_lat_deg       ### Scale degrees to radians

    surf_lon_rad = rpd * surf_lon_deg
    surf_lat_rad = rpd * surf_lat_deg

    ####################################################################
    ### End of input processing, make calculations (5 steps)
    ####################################################################

    ### Convert TOMS and surface points geodetic positions to ECEF vectors
    toms_vec = spice.georec(toms_lon_rad,toms_lat_rad,toms_alt_km,re,f)
    surfPoint = spice.georec(surf_lon_rad,surf_lat_rad,0.,re,f)

    ### Get normal at surface point, ECEF unit vector
    uvSurfNormal = spice.surfnm(re,re,rp,surfPoint)

    ### Get cosine of incidence angle (angle between Sun & surface normal vector)
    mu = spice.vdot(uvEarth2Sun,uvSurfNormal)

    if mu <= 0.:
      print('%s  =>  %7s' % (linestrip,'Surface point is dark',))   ### Sun is below surface horizon
      continue

    uvReflect = spice.vsub(spice.vscl(2.*mu,uvSurfNormal),uvEarth2Sun)  ### Get specular reflection vector

    glint_angle_deg = dpr*spice.vsep(uvReflect,spice.vsub(toms_vec,surfPoint))
    print('%s  =>  %7.2f %s' % (linestrip,glint_angle_deg,'=Inputs[TOMS(alt,lon,lat),(Earth2Sun),Surface(lon,lat),UTC],GlintAngle',))


"""
- Longitude and Latitude in degrees
- Altitude in metres

      [Altitude,Lon,Lat;Geodet]     [Earth-Sun Unit Vec, ECEF]   [SurfGeodLonLat]  [UTC]
data:    766000 -10.743 -27.129   -.2577401 .8836004 -.3909224     -10.01 -26.768  2001-01-01T12:12:53
data:    766000 -10.743 -27.129   -.2577401 .8836004 -.3909224      -2.76 -25.307  2001-01-01T12:12:53
data:    766000 -10.743 -27.129   -.2577401 .8836004 -.3909224       2.76 -25.307  2001-01-01T12:12:53
data:    766000 -10.743 -27.129   -.2577401 .8836004 -.3909224      10.01 -26.768  2001-01-01T12:12:53
data:    766000 -10.743 -27.129   -.2577401 .8836004 -.3909224      30.01 -26.768  2001-01-01T12:12:53
data:    766000 -10.743 -27.129   -.2577401 .8836004 -.3909224      50.01 -26.768  2001-01-01T12:12:53
data:    766000 -10.743 -27.129   -.2577401 .8836004 -.3909224      70.01 -26.768  2001-01-01T12:12:53
data:    766000 -10.743 -27.129   -.2577401 .8836004 -.3909224      90.01 -26.768  2001-01-01T12:12:53
data:    766000 -10.743 -27.129   -.2577401 .8836004 -.3909224     110.01 -26.768  2001-01-01T12:12:53
data:    766000 -10.743 -27.129   -.2577401 .8836004 -.3909224     130.01 -26.768  2001-01-01T12:12:53

Meta-kernel:

\begindata
KERNELS_TO_LOAD = (
  'naif0011.tls'
  'pck00010.tpc'
)
\begintext
"""
