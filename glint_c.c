#include <stdio.h>

#include "SpiceUsr.h"

/*

   1 23940U 96037A   12341.93476993  .00000273  00000-0  75967-4 0  1187
   2 23940 097.9131 164.1161 0029731 023.1886 337.0617 14.53048997873601
 */
//                        1         2         3         4         5         5         7
//                1234567890123456789012345678901234567890123456789012345678901234567890
static char lines[2][70] = { "1 23940U 96037A   12341.93476993  .00000273  00000-0  75967-4 0  1187"
                           , "2 23940 097.9131 164.1161 0029731 023.1886 337.0617 14.53048997873601"
                           };

// from http://naif.jpl.nasa.gov/pub/naif/toolkit_docs/FORTRAN/spicelib/ev2lin.html
static SpiceDouble geophs[8] = { 1.082616e-3, -2.53881e-6, -1.65597e-6   // J2, J3, J4
                               , 7.43669161e-2                           // KE
                               , 120.0e0, 78.0e0                         // QO, SO
                               , 6378.135e0                              // ER
                               , 1.0                                     // AE
                               };

int
main() {
SpiceDouble et0;
SpiceChar utc0[25];
SpiceChar utc[25];
SpiceDouble elems[10];

SpiceDouble deltaET;
SpiceDouble et;
SpiceDouble state[6];
SpiceDouble r, lat, lon;
SpiceDouble dpr = dpr_c();
int i;

  furnsh_c("naif0011.tls");
  getelm_c( 1996, 70, lines, &et0, elems);
  et2utc_c(et0,"ISOC",3,25, utc0);
  printf("\n%s\n%s\n%s\n\n", utc0, lines[0], lines[1]);

  for (i=0; i<10; ++i) {
    printf("%s%17.8e", (i%5) ? "" : "\n", elems[i]);
  }
  printf("%s", "\n\n");

  for ( deltaET=0.; deltaET<(225*60.); deltaET+=300) {
    et = et0 + deltaET;
    ev2lin_(&et, geophs, elems, state);
    reclat_c( state, &r, &lat, &lon);
     et2utc_c(et,"ISOC",3,25, utc);
    printf( "%s %10.3lf %8.3lf %8.3lf\n", utc, r, lat*dpr, lon*dpr);
  }
  return 0;
}
