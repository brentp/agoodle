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
