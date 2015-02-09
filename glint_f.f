      programglint_f
      implicitnone
      character*69 lines(2)

      character*40 utc0, utc
      doubleprecision et0, et, state(6), r, lat, lon
      doubleprecision elems(10)
      integer deltaET

C     from http://naif.jpl.nasa.gov/pub/naif/toolkit_docs/FORTRAN/spicelib/ev2lin.html
      doubleprecision geophs(8) /
     &   1.082616d-3, -2.53881d-6, -1.65597d-6   !! J2, J3, J4
     & , .43669161d-2                            !! KE
     & , 120.0d0, 78.0d0                         !! QO, SO
     & , 6378.135d0                              !! ER
     & , 1D0                                     !! AE
     & /

      doubleprecision dpr
      external dpr
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
      lines(1) = '1 23940U 96037A   12341.93476993  '
     &        // '.00000273  00000-0  75967-4 0  1187'
      lines(2) = '2 23940 097.9131 164.1161 0029731 '
     &        // '023.1886 337.0617 14.53048997873601'
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
      call furnsh('naif0011.tls')
      call getelm(1996,lines,et0,elems)

      call et2utc(et0, 'ISOC', 3, utc0)
      print'(/a23/a/a/a/)', utc0, lines
      print'(/2(5(1pe17.8)/))', elems

      do deltaET=0,225 * 60 - 1,300
        et = et0 + deltaET
        call ev2lin(et,geophs,elems,state)
        call reclat(state,r,lat,lon)
        call et2utc(et,'ISOC',3,utc)
        print'(a23,1x,f10.3,1x,f8.3,1x,f8.3)',utc,r,lat*dpr(),lon*dpr()
      enddo
      end
