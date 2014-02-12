
from setuptools import setup, find_packages

from ident_viewer.version import version

setup(name="ident_viewer",
      packages=find_packages(exclude=["tests"]),
      version="%d.%d.%d" % version,
      entry_points={
          "gui_scripts": ["ivi = ident_viewer.cmdline:main",
                         ]

      },
      include_package_data=True,
      zip_safe=False,
      install_requires=[]
    )
