from distutils.core import setup
from Cython.Build import cythonize

setup(
      name = 'wraptest',
    ext_modules = cythonize("test.pyx", language="c++"),
)
