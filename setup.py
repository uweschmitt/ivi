from setuptools import setup, find_packages
from distutils.extension import Extension
import numpy

ext_modules = [
    Extension("ivi.optimizations",
              ["ivi/optimizations.c"],
              include_dirs=[numpy.get_include()]
              )
]

version = (0, 0, 3)

setup(name="ivi",
      packages=find_packages(exclude=["tests"]),
      version="%d.%d.%d" % version,
      entry_points={
          "gui_scripts": ["ivi = ivi.cmdline:main",
                          "ivi.prepare = ivi.cmdline:prepare", ]

      },
      include_package_data=True,
      zip_safe=False,
      install_requires=["tables"],
      ext_modules=ext_modules,
      )
