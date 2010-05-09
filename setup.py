from setuptools import setup
from distutils.core import Extension


setup(name          = 'Agoodle',
      version       = '0.0.1',
      description   = 'use numpy with raster geo-data by way of GDAL',
      license       = 'MIT',
      keywords      = 'gis gdal numpy',
      url   = '',
      long_description = open('README.rst').read(),
      packages      = ['agoodle'],
      #install_requires = ['setuptools', 'numpy', 'gdal', 'matplotlib'],
      tests_require = ['nose'],
      test_suite = 'nose.collector',
      classifiers   = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: GIS'
        ],
)
