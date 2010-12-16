import numpy as np
import matplotlib.nxutils as nx
from osgeo import gdal
from osgeo import ogr, osr
import os.path as op


class RasterInfo(object):

    def __init__(self, raster):
        t = raster.GetGeoTransform()
        self.left  = t[0]
        self.xsize = t[1]
        self.top   = t[3]
        self.ysize = t[5]

        self.nx = raster.RasterXSize
        self.ny = raster.RasterYSize

        self.bottom = self.top  + self.ysize * self.ny
        self.right  = self.left + self.xsize * self.nx

        assert self.right > self.left, "bounds are messed up"
        if self.bottom > self.top:
            self.bottom, self.top = self.top, self.bottom
            self.ysize *= -1
        #assert self.bottom < self.top

    def __repr__(self):
        fmt = "RasterInfo(extent=(%.2f, %.2f, %.2f, %.2f)"
        fmt += ", pixel=(%i, %i), gridsize=(%i, %i))"
        return fmt % (self.left, self.bottom, self.right, self.top,\
                           self.xsize, self.ysize, self.nx, self.ny)

    @property
    def extent(self):
        return (self.left, self.bottom, self.right, self.top)


class AGoodle(object):

    def __init__(self, filename):
        assert op.exists(filename), "%s does not exist" % filename
        self.filename = filename
        self.raster   = gdal.Open(filename)
        self.ri = self.raster_info = RasterInfo(self.raster)

    def __repr__(self):
        return "%s(\"%s\")" % (self.__class__.__name__, self.filename)

    def bbox_to_grid_coords(self, bbox):
        """
        given a bbox in real-world coordinates return the indexes into
        the .tif that will extract the data -- though note that ReadArray
        requires offset for the 3rd, 4th params, not xmax, ymax.
        also return the modified bbox, that exactly matches the grid coords."""
        bbox = list(bbox) # incase it's a tuple
        gt = self.ri
        if bbox[0] < gt.left: bbox[0] = gt.left
        if bbox[3] > gt.top:  bbox[3] = gt.top
        # TODO: trim to the other edges as well.

        tminx = (bbox[0] - gt.left)/ gt.xsize
        tmaxx = (bbox[2] - gt.left)/ gt.xsize
        tminy = (bbox[3] - gt.top) / gt.ysize
        tmaxy = (bbox[1] - gt.top) / gt.ysize
        assert tminx < tmaxx, ("min should be < max!", tminx, tmaxx)
        if tminy > tmaxy:
            (tminy, tmaxy) = (tmaxy, tminy)
        # round down for mins, and up for maxs to make sure the
        # requested extent is in the area requested.
        tminx, tminy = [max(int(round(t - 0.5)), 0) for t in (tminx, tminy)]
        tmaxx, tmaxy = [int(round(t + 0.5)) for t in (tmaxx, tmaxy)]
        if tmaxx > self.ri.nx: tmaxx = self.ri.nx
        if tmaxy > self.ri.ny: tmaxy = self.ri.ny
        cbbox = [tminx, tminy, tmaxx, tmaxy]
        assert cbbox[2] > cbbox[0] and cbbox[3] > cbbox[1], ("box out of order", cbbox)

        new_bbox = [None, None, None, None]
        new_bbox[0] = gt.left + cbbox[0] * gt.xsize
        new_bbox[2] = gt.left + cbbox[2] * gt.xsize
        new_bbox[1] = gt.top + cbbox[3] * gt.ysize
        new_bbox[3] = gt.top + cbbox[1] * gt.ysize
        assert new_bbox[3] > new_bbox[1], (new_bbox, "out of order")

        return cbbox, new_bbox

    def read_array_bbox(self, bbox=None):
        """given a bbox : (xmin, ymin, xmax, ymax)
        return a numpy array of that extent"""
        if bbox is None:
            bbox = self.ri.extent
        idxs, new_bbox = self.bbox_to_grid_coords(bbox)
        a = self.raster.ReadAsArray(idxs[0], idxs[1],\
                idxs[2] - idxs[0], idxs[3] - idxs[1])

        return goodlearray(a, self, new_bbox)

    def summarize_wkt(self, wkt, wkt_epsg=None, this_epsg=None):
        """
        encapsulate the common task of querying a raster with a wkt polygon
        returns a dictionary of class : area.
        where class is the integer value in the raster data store and area is
        the area in units of the raster.
        Likely, one will convert the integer classes into their human-readable names before
        presenting.
        """
        this_sr = osr.SpatialReference()
        wkt_sr = osr.SpatialReference()
        if this_epsg is None:
            pr = self.raster.GetProjection()
            this_sr.ImportFromWkt(pr)
        else:
            this_sr.ImportFromEPSG(this_epsg)
        if wkt_epsg is None:
            pr = self.raster.GetProjection()
            wkt_sr.ImportFromWkt(pr)
        else:
            wkt_sr.ImportFromEPSG(wkt_epsg)

        pts, bbox = points_from_wkt(wkt, wkt_epsg, this_sr)
        a = self.read_array_bbox(bbox)
        a.mask_with_poly(pts, copy=False)
        return a.do_stats()

    def circle_mask(self, cradius, mask):
         xs, ys = np.mgrid[-cradius:cradius + 1
                            , -cradius:cradius + 1]

         d = np.sqrt(xs **2 + ys ** 2)
         d = (d  <= cradius).astype(np.int)
         return d

    def read_array_pt_radius(self, x, y, radius=50000, mask=0, do_mask=True):
        ri = self.ri
        cell_x = (x - ri.left)/ ri.xsize - (radius / ri.xsize)
        cell_y = (ri.top - y)/ abs(ri.ysize) + (radius / ri.ysize)

        cell_x, cell_y = int(round(cell_x)), int(round(cell_y))
        xsize = int(round(2 * radius / ri.xsize + 0.5))
        ysize = abs(int(round(2 * radius / ri.ysize + 0.5)))
        # it has to be an odd number for the masking.
        if not xsize % 2: xsize += 1
        if not ysize % 2: ysize += 1
        a = self.raster.ReadAsArray(cell_x, cell_y, xsize, ysize)
        if do_mask:
            m = self.circle_mask(xsize / 2, mask=mask)
            #assert False, (cell_x, cell_y, ri.xsize, ri.ysize)
            return goodlearray(m * a, self, [x - radius, y - radius, x + radius, y + radius])
        else:
            return goodlearray(a, self, [x - radius, y - radius, x + radius, y + radius])



class goodlearray(np.ndarray):
    """
    an enhanced numpy array class that keeps geographic information
    allowing simple querying of an array with real world coordinates

       gda.rw(-121.2, 43.5)
    """

    def __new__(subtype, data, agoodle, extent, dtype=None, copy=False):
        arr = np.array(data, dtype=dtype, copy=copy).view(subtype)
        arr.agoodle = agoodle
        arr.extent = extent
        return arr

    def rw2index(self, rx, ry):
        bbox = self.extent
        #assert bbox[0] <= rx <= bbox[2] \
        #   and bbox[1] <= ry <= bbox[3],\
        #       ('point out of grid', bbox, (rx, ry))

        xrng = float(bbox[2] - bbox[0])
        yrng = float(bbox[3] - bbox[1])
        x = (rx - bbox[0]) / xrng * self.shape[1]
        y = (bbox[3] - ry) / yrng * self.shape[0]
        #y = (ry - bbox[1]) / yrng * self.shape[0]
        ix, iy = int(x), int(y)
        if ix == self.shape[1]: ix -= 1
        if iy == self.shape[0]: iy -= 1

        assert ix < self.shape[1], (ix, self.shape[1])
        assert iy < self.shape[0], (iy, self.shape[0])

        #print ix, iy
        return ix, iy

    def rw(self, rx, ry):
        """take real world coordinate and read the value at
        that coord"""
        ix, iy = self.rw2index(rx, ry)
        return self[iy, ix]

    def mask_with_poly(self, verts, mask_value=0, copy=True):
        """verts is in real-world coordinates in same
        projection as this array.
        if copy is false, a new array is not created.
        """
        #TODO: sample if the array is too big.
        assert self.shape[0] * self.shape[1] < 4000000
        iverts = np.array([self.rw2index(v[0], v[1]) for v in verts])
        ys, xs = np.indices(self.shape)
        xys = np.column_stack((xs.flat, ys.flat))
        insiders  = nx.points_inside_poly(xys, iverts)
        outsiders = xys[(insiders == 0)]

        if copy:
            b = self.copy()
            b[(outsiders[:, 1], outsiders[:, 0])] = mask_value
            return b
        self[(outsiders[:, 1], outsiders[:, 0])] = mask_value

    def do_stats(self, exclude=(0, )):
        """ do some stats on the integer types in the array.
        returns the area of cells for each type found in the array.
        you can use this after masking to only calc inside the polygon.
        """
        raster_info = self.agoodle.raster_info
        classes = np.unique(self)
        cell_area = abs(raster_info.xsize * raster_info.ysize)
        stats = {}
        for cls in (c for c in classes if c not in exclude):
            stats[cls] = len(self[self == cls]) * cell_area
        return stats

    def to_raster(self, filename, driver='GTiff'):

        from osgeo import gdal_array
        # convert from numpy type to gdal type.
        gdal_type = dict((v, k) for (k, v) \
                in gdal_array.codes.items())[self.dtype.type]

        # make it so we can loop over 3rd axis.
        if len(self.shape) == 2:
            a = self[:, :, np.newaxis]
        else:
            a = self
        bbox = self.extent
        ri = self.agoodle.ri
        d = gdal.GetDriverByName(driver)

        # NOTE: switch of shape[0] and [1] !!!!
        tif = d.Create(filename, a.shape[1], a.shape[0], a.shape[2], gdal_type)
        xsize = (bbox[2] - bbox[0]) / (self.shape[1])
        ysize = (bbox[1] - bbox[3]) / (self.shape[0])
        # could be a bit off since we had to round to pixel.
        assert abs(xsize - ri.xsize) < 1
        assert abs(ysize - ri.ysize) < 1, (ysize, ri.ysize, xsize, ri.xsize)
        tif.SetGeoTransform([bbox[0], xsize, 0, bbox[3], 0, ysize])
        for i in range(a.shape[2]):
            b = tif.GetRasterBand(i + 1)
            ct = self.agoodle.raster.GetRasterBand(i + 1).GetRasterColorTable()
            if ct:
                b.SetRasterColorTable(ct)
            gdal_array.BandWriteArray(b, a[:, :, i])
        tif.SetProjection(self.agoodle.raster.GetProjection())
        return tif


def points_from_wkt(wkt, from_epsg, to_epsg):
    """
    send in the wkt for a polygon and get back the
    points and the bbox that contains those points.
    `from_epsg` and `to_epsg` determine how to reproject
    the points. this can be used if the wkt is in a projection
    different from the raster to be queried.
    """
    g = ogr.CreateGeometryFromWkt(wkt)
    if isinstance(from_epsg, (long, int)):
        ifrom = osr.SpatialReference(); ifrom.ImportFromEPSG(from_epsg)
    else:
        ifrom = from_epsg
    if isinstance(ifrom, (long, int)):
        ito = osr.SpatialReference(); ito.ImportFromEPSG(to_epsg)
    else:
        ito = to_epsg
    g.AssignSpatialReference(ifrom)
    g.TransformTo(ito)

    # assume it's a polygon, get the outer ring.
    ring = g.GetGeometryRef(0)
    pts = []
    for i in range(ring.GetPointCount()):
        x, y, z = ring.GetPoint(i)
        pts.append((x, y))
    pts = np.array(pts)
    bbox = (pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max())
    return pts, bbox
