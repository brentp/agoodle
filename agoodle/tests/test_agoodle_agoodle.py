import unittest
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from agoodle import AGoodle
import numpy as np

class TestRasterInfo(unittest.TestCase):
    def setUp(self):
        path = os.path.dirname(__file__)
        self.tifpath = os.path.join(path, 'data', 'raster.tif')
        self.ag = AGoodle(self.tifpath)
        self.ri = self.ag.ri

    def test_extent(self):
        assert len(self.ri.extent) == 4

    def test_object_initialization(self):
        pass

class TestAGoodle(unittest.TestCase):
    def setUp(self):
        path = os.path.dirname(__file__)
        self.tifpath = os.path.join(path, 'data', 'raster.tif')
        self.ag = AGoodle(self.tifpath)

    def test_bbox_to_grid_coords(self):
        e = self.ag.ri
        rx = e.right - e.left
        ry = e.top - e.bottom
        bbox = (e.left + rx/2.1, e.bottom + ry/2.1, e.right - rx/2.1, e.top - ry/2.1)
        coords, new_bbox = self.ag.bbox_to_grid_coords(bbox)
        assert 0 < coords[0] < coords[2] < self.ag.ri.ny
        assert 0 < coords[1] < coords[3] < self.ag.ri.nx

        for o, n in zip(bbox, new_bbox):
            assert abs(o - n) < 20, (o, n)


    def test_object_initialization(self):
        self.ag = AGoodle(self.tifpath)
        self.assert_(isinstance(self.ag, AGoodle))

    def test_read_array_bbox(self):
        e = self.ag.ri
        rx = e.right - e.left
        ry = e.top - e.bottom
        bbox = (e.left + rx/2.1, e.bottom + ry/2.1, e.right - rx/2.1, e.top - ry/2.1)
        a = self.ag.read_array_bbox(bbox)
        assert hasattr(a, 'agoodle')

        # and with full extent
        a = self.ag.read_array_bbox()
        assert hasattr(a, 'agoodle')

class TestSummarize(unittest.TestCase):

    def setUp(self):
        path = os.path.dirname(__file__)
        self.tifpath = os.path.join(path, 'data', 'z.tif')
        self.ag = AGoodle(self.tifpath)

    def test_summarize(self):
        """
        bbox = self.ag.ri.extent
        xcoords = np.linspace(bbox[0], bbox[2], 6)
        ycoords = list(np.linspace(bbox[1], bbox[3], 6))
        ycoords = ycoords[3:] + ycoords[:3]
        verts = zip(xcoords, ycoords)
        verts.append(verts[0])
        verts = np.array(verts)
        print >>sys.stderr, verts
        from shapely.geometry import Polygon
        wkt = Polygon(verts).wkt
        print >> sys.stderr, wkt
        return
        """
        wkt = """POLYGON ((-13249847.8545559067279100 4564878.5321548320353031, -13236254.9522339217364788 4581493.7669484084472060, -13222662.0499119367450476 4598109.0017419848591089, -13209069.1475899536162615 4515032.8277741018682718, -13195476.2452679686248302 4531648.0625676782801747, -13181883.3429459836333990 4548263.2973612546920776, -13249847.8545559067279100 4564878.5321548320353031))"""
        ag = self.ag
        summary = ag.summarize_wkt(wkt)
        #print >>sys.stderr, summary
        possible = np.unique(ag.read_array_bbox()).tolist()

        # the classes returned from the query has to be a subset of the total
        #classes in the raster
        self.assert_(set(summary.keys()).issubset(possible))

        ext = ag.ri.extent
        raster_area = (ext[2] - ext[0]) * (ext[3] - ext[1])
        self.assert_(sum(summary.values()) < raster_area)


class TestGoodlearray(unittest.TestCase):
    def setUp(self):
        path = os.path.dirname(__file__)
        self.tifpath = os.path.join(path, 'data', 'z.tif')
        self.ag = AGoodle(self.tifpath)
        extent = self.ag.ri.extent
        #rx, ry = e.right - e.left, e.top - e.bottom
        #bbox = (e.left + rx/2.1, e.bottom + ry/2.1, e.right - rx/2.1, e.top - ry/2.1)
        self.a = self.ag.read_array_bbox(extent)

    def test_mask_with_poly(self):
        a = self.a
        bbox = a.extent
        xcoords = np.linspace(bbox[0], bbox[2], 6)
        ycoords = list(np.linspace(bbox[1], bbox[3], 6))
        ycoords = ycoords[3:] + ycoords[:3]
        verts = zip(xcoords, ycoords)
        verts.append(verts[0])
        verts = np.array(verts)

        b = a.mask_with_poly(verts, copy=True, mask_value=0)
        assert b.sum() < a.sum()
        assert b.shape == a.shape


    def test_rw(self):
        self.a.to_raster('test_ost.tif')
        assert os.path.exists('test_ost.tif')


    def test_rw2index(self):
        a = self.a
        bbox = a.extent
        ix, iy = a.rw2index(bbox[0], bbox[1])
        assert ix == 0 
        assert iy == a.shape[0] - 1, (iy, a.shape[0])
        ix, iy = a.rw2index(bbox[2], bbox[3])
        assert iy == 0 
        assert ix == a.shape[1] - 1, (ix, a.shape[1])

    def tearDown(self):
        try: os.unlink('test_ost.tif')
        except: pass

if __name__ == '__main__':
    unittest.main()
