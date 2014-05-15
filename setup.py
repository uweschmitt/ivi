from setuptools import setup, find_packages
from distutils.extension import Extension
import numpy

ext_modules = [
    Extension("ident_viewer.optimizations",
              ["ident_viewer/optimizations.c"],
              include_dirs=[numpy.get_include()]
              )
]

version = (0, 0, 2)

setup(name="ident_viewer",
      packages=find_packages(exclude=["tests"]),
      version="%d.%d.%d" % version,
      entry_points={
          "gui_scripts": ["ivi = ident_viewer.cmdline:main",
                          "ivi.prepare = ident_viewer.cmdline:prepare", ]

      },
      include_package_data=True,
      zip_safe=False,
      install_requires=["tables"],
      ext_modules=ext_modules,
      )
