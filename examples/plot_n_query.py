import os.path as op
import numpy as np
from agoodle import AGoodle
import matplotlib
matplotlib.use('Agg')
import pylab

path = op.join(op.dirname(__file__), "..", "agoodle", "tests", "data", "z.tif")
g = AGoodle(path)
e = g.raster_info
rx = e.right - e.left
ry = e.top - e.bottom

# take a subset.
bbox = (e.left + rx/2.1, e.bottom + ry/2.1,
        e.right - rx/2.1, e.top - ry/2.1)

a = g.read_array_bbox(bbox)
assert hasattr(a, 'agoodle')

# save to a new tif.
a.to_raster('z.tif')

bbox = a.extent

# use rw2index to convert to array indexes.
ix, iy = a.rw2index(bbox[0], bbox[1])
assert ix == 0
ix, iy = a.rw2index(bbox[2], bbox[3])
assert ix == a.shape[1] - 1, (ix, a.shape[1])


# make some query coordinates.
xcoords = np.linspace(bbox[0], bbox[2], 5)
ycoords = list(np.linspace(bbox[1], bbox[3], 5))
ycoords = ycoords[2:] + ycoords[:2]
verts = zip(xcoords, ycoords)
verts.append(verts[0])
verts = np.array(verts)

# hack up the figure.
pylab.figure(figsize=(2, 6))
pylab.subplot(311)
pylab.title("original")
pylab.xticks([]); pylab.yticks([])
pylab.imshow(a, extent=(bbox[0], bbox[2], bbox[1], bbox[3]))
pylab.subplot(312)
pylab.title("polygon")
ax, = pylab.plot(verts[:, 0], verts[:, 1])
ax.axes.set_aspect(1.0)
ax.axes.set_xticks([])
ax.axes.set_yticks([])
pylab.xlim(bbox[0], bbox[2])
pylab.ylim(bbox[1], bbox[3])

b = a.mask_with_poly(verts, copy=True, mask_value=0)
pylab.subplot(313)
pylab.title("masked to poly")
pylab.xticks([]); pylab.yticks([])
pylab.imshow(b, extent=(bbox[0], bbox[2], bbox[1], bbox[3]))
pylab.savefig('/var/www/t/z.png')
pylab.show()
