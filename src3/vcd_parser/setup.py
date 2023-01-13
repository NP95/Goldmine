########### BUILD COMMAND #############
# python setup.py build_ext --inplace #
########### BUILD COMMAND #############


from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

setup(
        name = 'VCD Parse TimeFrames App',
        version = '0.1',
        ext_modules = cythonize('parse_timeframes.pyx'),
        )