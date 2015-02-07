#! /usr/local/bin/python

import os, sys, string, numpy, re, decimal

class PDSImage:
    """PDSImage.

    Read multi-band NASA PDS <http://pds.jpl.nasa.gov/documents>
    image file, query header information and extract binary image 
    data in a format suitable for PIL.  Works for Pathfinder and 
    Mars Exploration Rover images, maybe others.

    Examples:
    
    QUERY PDS HEADER
    ================
    
    from PDSImage import *
    print PDSImage('648405R.IMG').getAttribs('/image/sample_bit_mask')
    
    CREATE CSV SPREADSHEET FROM PDSImage
    ====================================
    
    from PDSImage import *
    import csv
    p = PDSImage('648405R.IMG')
    w = csv.writer(open('648405R.IMG', 'w'))
    
    for i in p._im:      ### N.B. ._im disabled
        w.writerow(i)
        
    CONVERT PDSimage TO TIFF USING PIL
    ==================================
    
    import Image as I
    from PDSImage import *
    
    p = PDSImage('648405R.IMG')
    I.fromstring('L', p.getDimensions(), p.getImage(), 'raw', 'L').save('p.tif')

    History:

    2009-10 BTCarcich, Cornell University
    - Downloaded from SourceForge
    - Modified to make more general
      - Recursive builing and searching of ._attribs dict
        - Allow array of elements in ._attribs objs, access via .../[n]
      - Commented unused members ._lut, ._zeroarray
      - Commented members ._im, ._im8
      - Commented several functions
    2010-06
      - Multiple bands allowed
      - Bugs in parser have been fixed
    
    """

    def __init__(self, fn='', dim=(1024,1024,), seek=0):
        """Initialize PDSImage.
        
        Keyword arguments:
        fn -- file name (default '')
        dim -- x,y tuple (default (1024,1024))
        
        With no arguments, creates an empty 1024x1024 PDSImage.
        """

        self._fn = fn
        self._seek = seek
        self._attribs = {}
        self._RawPDSLabel = []
        ###self._lut = []
        self._dim = dim
        self._rb = 0
        
        self.signedRe = [ re.compile("^SIGNED"), re.compile("_SIGNED") ]

        ###self._zeroarray = numpy.zeros(dim)
        ###self._im = numpy.zeros(dim, dtype=numpy.int16)
        ###self._im8 = numpy.zeros(dim, dtype=numpy.int8)
        self._NF = ['N/A', 'NULL', 'UNK']   

        ### Aliases from PDS StdRef Appendix C
        self._ali = { 'INTEGER': 'MSB_INTEGER' \
                    , 'MAC_INTEGER': 'MSB_INTEGER' \
                    , 'SUN_INTEGER': 'MSB_INTEGER' \
                    \
                    , 'UNSIGNED INTEGER': 'MSB_UNSIGNED_INTEGER' \
                    , 'MAC_UNSIGNED_INTEGER': 'MSB_UNSIGNED_INTEGER' \
                    , 'SUN_UNSIGNED_INTEGER': 'MSB_UNSIGNED_INTEGER' \
                    \
                    , 'PC_INTEGER': 'LSB_INTEGER' \
                    , 'VAX_INTEGER': 'LSB_INTEGER' \
                    \
                    , 'PC_UNSIGNED_INTEGER': 'LSB_UNSIGNED_INTEGER' \
                    , 'VAX_UNSIGNED_INTEGER': 'LSB_UNSIGNED_INTEGER' \
                    \
                    , 'FLOAT': 'IEEE_REAL' \
                    , 'REAL': 'IEEE_REAL' \
                    , 'MAC_REAL': 'IEEE_REAL' \
                    , 'SUN_REAL': 'IEEE_REAL' \
                    \
                    , 'COMPLEX': 'IEEE_COMPLEX' \
                    , 'MAC_COMPLEX': 'IEEE_COMPLEX' \
                    , 'SUN_COMPLEX': 'IEEE_COMPLEX' \
                    \
                    , 'VAX_DOUBLE': 'VAX_REAL' \
                    }

        ### border:  byte order MSB LSB
        ### ctyp:  data type uint int float comples BIT_STRING
        ### flttyp:  floating point type IEEE PC VAX VAXG

        self._data_types = \
        { 'MSB_INTEGER':  { 'border': 'big', 'ctyp': 'int' } \
        , 'MSB_UNSIGNED_INTEGER':  { 'border': 'big', 'ctyp': 'uint' } \
        , 'LSB_INTEGER':  { 'border': 'little', 'ctyp': 'int' } \
        , 'LSB_UNSIGNED_INTEGER':  { 'border': 'little', 'ctyp': 'uint' } \
        , 'IEEE_REAL':  { 'border': 'big', 'ctyp': 'float', 'flttyp': 'IEEE' } \
        , 'IEEE_COMPLEX':  { 'border': 'big', 'ctyp': 'complex', 'flttyp': 'IEEE' } \
        , 'PC_REAL':  { 'border': 'little', 'ctyp': 'float', 'flttyp': 'PC' } \
        , 'PC_COMPLEX':  { 'border': 'little', 'ctyp': 'complex', 'flttyp': 'PC' } \
        , 'VAX_REAL':  { 'border': 'little', 'ctyp': 'float', 'flttyp': 'VAX' } \
        , 'VAX_COMPLEX':  { 'border': 'little', 'ctyp': 'complex', 'flttyp': 'VAX' } \
        , 'VAXG_REAL':  { 'border': 'little', 'ctyp': 'float', 'flttyp': 'VAXG' } \
        , 'VAXG_COMPLEX':  { 'border': 'little', 'ctyp': 'complex', 'flttyp': 'VAXG' } \
        , 'MSB_BIT_STRING':  { 'border': 'big', 'ctyp': 'BIT_STRING' } \
        , 'LSB_BIT_STRING':  { 'border': 'little', 'ctyp': 'BIT_STRING' } \
        , 'UNKNOWN':  { 'border': 'UNKNOWN', 'ctyp': 'UNKNOWN', 'flttyp': 'UNKNOWN' } \
        }

        if fn == '':
            self._LINENUM = 0
        else:
            self.getPDSFile(fn)


    ####################################################################

    def parseDataType(self,ptrKwdArg='image'):
        """Convert OBJECT = <keyword> stanza into data description"""

        try:

            ptrKwd=ptrKwdArg.upper()

            ### Check for pointer and object

            if not (ptrKwd in self._pointers):
                raise AssertionError(2,'No pointer ^'+ptrKwd)
            if not (ptrKwd in self._attribs):
                raise AssertionError(2,'No OBJECT '+ptrKwd)

            obj=self.getAttribs(ptrKwd)
            if not (type(obj) is type({})):
                raise AssertionError(2,ptrKwd + ' is not an OBJECT')

            ### Prepare to get keywords from object

            ps=ptrKwd+'/'

            ############################################################
            ### DATA_TYPE or SAMPLE_TYPE

            kwdType = self.getAttribs(ps+'sample_type')
            if not kwdType:
                kwdType = self.getAttribs(ps+'data_type')
            if not kwdType:
                raise AssertionError(2 \
                  ,'DATA_/SAMPLE_TYPE not found in OBJECT ' + ptrKwd)

            if kwdType in self._ali:         ### Dereference alias
                kwdType = self._ali[kwdType]

            if not type(kwdType) is type(''):
                raise AssertionError(2 \
                  ,'DATA_/SAMPLE_TYPE is not string in OBJECT ' + ptrKwd)

            if not (kwdType in self._data_types):
                raise AssertionError(2 \
                  ,'DATA_/SAMPLE_TYPE is not valid in OBJECT ' + ptrKwd)

            rtn = self._data_types[kwdType]

            ############################################################
            ### ITEM_BYTES or SAMPLE_BITS or ITEM_BITS

            bytpp = self.getAttribs(ps+'item_bytes')

            if bytpp is None:
                bitpp = self.getAttribs(ps+'SAMPLE_BITS')
            else:
                bitpp = bytpp * 8

            if bitpp is None:
                bitpp = self.getAttribs(ps+'ITEM_BITS')

            if bitpp is None:
                raise AssertionError(2 \
                ,'ITEM_BYTES/SAMPLE_BITS/ITEM_BITS not in OBJECT ' + ptrKwd)

            if bytpp is None:
                bytpp = bitpp / 8

            if bitpp != (8*bytpp):
                raise AssertionError(2 \
                ,'Invalid SAMPLE_BITS/ITEM_BITS in OBJECT ' + ptrKwd)

            rtn['bitpp'] = bitpp
            rtn['bytpp'] = bytpp

            ### ITEMS or LINE_SAMPLES, LINES

            itms = self.getAttribs(ps+'items')
            if itms is None:
                bands = self.getAttribs(ps+'bands')
                if bands is None or bands is 1:
                  rtn['dim'] = ( self.getAttribs(ps+'line_samples') \
                               , self.getAttribs(ps+'lines') \
                               )
                else:
                  rtn['dim'] = ( self.getAttribs(ps+'line_samples') \
                               , self.getAttribs(ps+'lines') \
                               , self.getAttribs(ps+'bands') \
                               )
            else:
                rtn['dim'] = ( itms, )

            pfxb = self.getAttribs(ps+'line_prefix_bytes')
            if pfxb is None: pfxb = 0

            sfxb = self.getAttribs(ps+'line_suffix_bytes')
            if sfxb is None: sfxb = 0

            rtn['pfxsfxbyt'] = ( pfxb, sfxb )

            rtn['success'] = True
            rtn['status'] = 'OK'

        except:
            rtn = self._data_types['UNKNOWN']
            rtn['dim'] = (None)        ### Dimensions
            rtn['ctyp'] = 'NoneType'   ### numpy data type
            rtn['bitpp'] = 0           ### BITs Per Pixel
            rtn['bytpp'] = 0           ### BYTes Per Pixel
            rtn['pfxsfxbyt'] = (0,0)   ### line (Prefix,Suffix) bytes
            rtn['success'] = False
            rtn['status'] = 'FAILED'
            rtn['except'] = sys.exc_info()
            raise

        return rtn


    ####################################################################

    def getPointerToPath(self,ptrKwdArg='image'):
        """Convert pointer to readable filename and record number."""

        ### TODO:
        ### - Handle special case: ^OBJ = N <BYTES>
        ### - Make parser more robust

        try:

            ptrKwd=ptrKwdArg.upper()

            if not (ptrKwd in self._pointers):
                raise AssertionError(2,'No pointer ^'+ptrKwd)
            if not (ptrKwd in self._attribs):
                raise AssertionError(2,'No OBJECT '+ptrKwd)

            if re.search('^[("]', self._pointers[ptrKwd]):
                s = self.getAttribs('^'+ptrKwd).split(',')
                relfn = s[0].strip(' "')
                if len(s) > 1:
                    recNum = int(s[1].strip(' "'))
                else:
                    recNum = 1
                mo = re.search('[A-Z0-9_.]*$',self._fn.upper())
                if mo:
                    pfx = self._fn[:mo.start()]
                else:
                    pfx = ''
                fn = None
                tmpFn = pfx + relfn.lower()
                if os.path.exists(tmpFn):
                    fn = tmpFn
                else:
                    tmpFn = pfx + relfn.upper()
                    if os.path.exists(tmpFn):
                        fn = tmpFn
                if not fn:
                    raise AssertionError(2 \
                    ,'^'+ptrKwd+' pointer file not found '+pfx+relfn)
            else:
                fn=self._fn
                recNum = self.getAttribs('^'+ptrKwd)

            f = open(fn, 'rb')
            f.close()

        except:
            return None, None, sys.exc_info()

        return fn, recNum, sys.exc_info()


    ####################################################################

    def getObjectData(self,ptrKwdArg='image'):
        """Read IMAGE or HISTOGRAM data

           - Argument is pointer keyword (e.g. IMAGE, IMAGE_HISTOGRAM)
           - Returns 3-tuple:
             - on failure:  (None, sys.exc_info(), None)
             - on success:  (data, linePrefixBytes, lineSuffixBytes)
               - Data will be a numpy.ndarray
               - if present, prefix &/or suffix will be numpy.ndarray
                 - either/both may be None

        """

        try:

            ############################################################
            ### Parse data type from DATA_TYPE or SAMPLE_TYPE
            ###   => int/real/complex/bit_string

            parsed = self.parseDataType( ptrKwdArg)

            if not parsed['success']:
                raise parsed['except']

            ############################################################
            ### Convert parsed info to numpy.dtype

            npDT = numpy.dtype( parsed['ctyp'] + str(parsed['bitpp']))

            ############################################################
            ### Get filename pointer and object record number

            fn,recNum,exc = self.getPointerToPath(ptrKwdArg)
            if fn is None:
                raise exc

            rb = self.getAttribs('record_bytes')

            ############################################################
            ### Calculate sizes and offsets

            dim = parsed['dim']
            bytpp = parsed['bytpp']
            pfxsfx = parsed['pfxsfxbyt']

            pfxb = pfxsfx[0]
            sfxb = pfxsfx[1]

            lenDim = len(dim)

            if lenDim == 1:
                bytSize = bytpp * dim[0]
                bytDim = (bytSize,)
                npShape = dim
            elif lenDim == 2:
                bytDim = (dim[1], pfxb+(bytpp*dim[0])+sfxb,)
                bytSize = bytDim[0] * bytDim[1]
                npShape = (dim[1],dim[0], )
            elif lenDim == 3:
                bytDim = (dim[2], dim[1], pfxb+(bytpp*dim[0])+sfxb, )
                bytSize = bytDim[0] * bytDim[1] * bytDim[2]
                npShape = (dim[2],dim[1],dim[0], )
            else:
                raise AssertionError(2 \
                  , str(len(dim))+' dimensions not yet implemented')

            ############################################################
            ### Read data as raw bytes

            f = open(fn,'rb')
            f.seek( rb * (recNum-1))
            raw = numpy.fromstring(f.read(bytSize),dtype=numpy.int8).reshape(bytDim)
            f.close()

            ############################################################
            ### Strip off prefix and suffix bytes

            pfxRaw=None
            sfxRaw=None
            if pfxb>0 and sfxb>0:
                pfxRaw=raw[:,:pfxb]
                sfxRaw=raw[:,-sfxb:]
                raw=raw[:,pfxb:-sfxb]
            elif pfxb>0:
                pfxRaw=raw[:,:pfxb]
                raw=raw[:,pfxb:]
            elif sfxb>0:
                sfxRaw=raw[:,-sfxb:]
                raw=raw[:,:-sfxb]

            if npDT is numpy.int8 or npDT is numpy.dtype('int8'):
                kwdType = self.getAttribs(ptrKwdArg+'/sample_type')
                if not kwdType:
                    kwdType = self.getAttribs(ptrKwdArg+'/data_type')
                for rgx in self.signedRe:
                  if rgx.search(kwdType): return raw, pfxRaw, sfxRaw
                return raw.astype(numpy.uint8), pfxRaw, sfxRaw

            ############################################################
            ### Convert bytes to numpy.dtype and reshape

            raw = raw.tostring()
            rtn = numpy.fromstring(raw, dtype=npDT).reshape(npShape)

            ############################################################
            ### Byteswap if necessary

            if parsed['border'] != sys.byteorder:
                rtn.byteswap(True)

        ################################################################
        ### Handle any exception above

        except:
            exc = sys.exc_info()
            return None, exc, None

        return rtn, pfxRaw, sfxRaw


    ####################################################################

    def getPDSFile(self, fn):
        """Read PDSImage file LABEL only"""

        self._LINENUM = 0
        self._pointers = {}

        f = open(fn, 'rb')
        f.seek(0,2)
        if f.tell() <= self._seek: return # Empty file
        f.seek(self._seek)

        self._attribs = self._downone( f)
        f.close()

        self._dim = (self.getAttribs('/image/line_samples'),self.getAttribs('/image/lines'))

        return


    ####################################################################

    def _downone( self, f):
        """Recursive PDS label parser"""

        foundEND=0
        foundEND_GO=0

        thisObjGrp={}

        while 1:

            lastTell = f.tell()
            fullline = f.readline()
            if "PDSIMAGE_DEBUG" in os.environ: sys.stdout.write( fullline)
            if lastTell == f.tell():
                break
            self._RawPDSLabel += fullline
            l = fullline.split()

            self._LINENUM += 1
            # Exit if this is actually a VICAR file...
            if self._LINENUM == 1 and (l+[''])[0][:7] == 'LBLSIZE':
                break

            # Skip blank lines and comments
            if not l:
                continue
            if l[0][:2] == '/*':
                continue
            if len(l)>1 and l[1][:2] == '/*':
              l = l[:1]

            # End of header?
            if len(l) == 1 and l[0] == 'END':
                foundEND=1
                break
            if l[0] == 'END_GROUP' or l[0] == 'END_OBJECT':
                foundEND_GO=1
                break

            # Where is the IMAGE?
            if len(l) > 2 and l[0] == 'RECORD_BYTES':
                self._rb = self.getAttribs('RECORD_BYTES')
            if len(l) > 2 and l[0] == 'LABEL_RECORDS':
                lr = int(l[2])
            if len(l) > 2 and l[0][0] == '^' :
                self._pointers[l[0][1:]] = l[2]

            # Flatten lines
            if  len(l) > 2 and  l[1] == '=' and l[2][0] == '"':
                if len(l[2]) == 1 and len(l) == 3:
                    l[2] += ' '
                while l[-1][-1] != '"':
                    lastTell=f.tell()
                    fullline = f.readline()
                    if lastTell==f.tell():
                        break
                    self._RawPDSLabel += fullline
                    l += fullline.split()
                if l[2] == '" ':
                    l[2] = '"'
                l[2] = string.join(l[2:])[1:-1]
                l = l[:3]    
            if  len(l) > 2 and  l[1] == '=' and l[2][0] == '(':
                while l[-1][-1] != ')':
                    lastTell=f.tell()
                    fullline = f.readline()
                    if lastTell==f.tell():
                        break
                    self._RawPDSLabel += fullline
                    l += fullline.split()
                l[2] = string.join(l[2:])[1:-1]
                l = l[:3]

            # Drill down into GROUPs and OBJECTs
            if l[0] == "GROUP" or l[0] == "OBJECT":
                kwd=l[2]
                if kwd in thisObjGrp:
                    if type(thisObjGrp[kwd]) is dict:
                        thisObjGrp[kwd] = [ thisObjGrp[kwd] ]
                        thisObjGrp['**listCOUNT@'+kwd] = 1
                    thisObjGrp[kwd] += [self._downone( f)]
                    thisObjGrp['**listCOUNT@'+kwd] += 1
                else:
                    thisObjGrp[kwd] = self._downone( f)

            # Add to top level attributes
            else:
                if len(l) > 2 and l[0] != "END_GROUP" and l[0] != "END_OBJECT" and l[0] != "END":
                    if re.match(r"^[\-\+]?([0-9]*\.)?[0-9]+([eE][\-\+]?[0-9]+)?\b$", l[2]):
                        if re.search(r"[.Ee]", l[2]):
                            l[2] = float(l[2])
                        elif (decimal.Decimal(l[2]) - int(decimal.Decimal(l[2]))) != 0:
                            l[2] = float(l[2])
                        else:
                            l[2] = int(decimal.Decimal(l[2]))
                    if len(l) > 2:# and l[2] not in self._NF:
                        thisObjGrp[l[0]] = l[2]


        if foundEND == 1:
          thisObjGrp['**foundEND']='TOP'
        elif foundEND_GO == 1:
          thisObjGrp['**foundEND']='NOTTOP'
        else:
          thisObjGrp['**foundEND']='NONE'

        return thisObjGrp


    def getAttribs(self, e=''):
        """Query PDS header.

        Keyword arguments:
        e -- search string (default '').  

        For member of PDS GROUP or OBJECT, separate GROUP name 
        and GROUP MEMBER name with '/'.  For instance, 
        'image/bands' (or even '/image/bands').

        Without arguments, returns header as a dictionary.  
        """
        s = 'self._attribs'
        if e == '':
            return self._attribs
        else:
            if e[0] == '/':
                e = e[1:]
            ###l = e.upper().split('/')
            l = e.split('/')
            for i in l:
                if i[:2] == '**':
                  iAtsign = i.find('@')
                  if iAtsign > -1:
                    i = i[:iAtsign] + i[iAtsign:].upper()
                else:
                  i=i.upper()
                if len(i) < 3 or i[:1] != '[' or i[-1:] != ']':
                  i='[\''+i+'\']'
                s = '%s%s' % (s, i)
            try:
                x = eval(s)
            except:
                x = None    ### Was ''
            return x

    def getRawPDSLabel(self):
        return self._RawPDSLabel

    def getAttribsDrilldown(self, attribArg=None, skipIfNone=False, e=''):

        if attribArg is None:
            if skipIfNone is True:
                return None
            return getAttribsDrillDown( attribArg=self._attribs, skipIfNone=True, e=e)

        if e == '':
            return attribArg

        try:
            l = e.upper().split('/')
            for i in l:
                if i == '':
                    continue
                ks=attribs.keys()
                if i in ks:
                  s = '%s[\'%s\']' % (s, i)
                x = eval(s)
        except:
            return self.getAttribsDrilldown( attribArg=None)

        return self.getAttribsDrilldown( attribArg=None)


    def getDimensions(self):
        """Get dimensions of OBJECT = IMAGE (tuple)."""
        return self._dim

