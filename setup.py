from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

setup(
  name = 'zhmalarm',
  ext_modules=cythonize([
    Extension("zhmalarm", ["zhmalarm.pyx", "zhmalarm_modules.c"],libraries=["pigpio","rt"]),
    ]),
)
