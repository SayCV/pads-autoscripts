import sys

from setuptools import find_packages, setup

if sys.version_info < (3, 0):
    sys.exit("Sorry, Python < 3.0 is not supported")

import re

VERSIONFILE = "padsprod/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

data_files = [
    ('', ['padsprod/config/*.tpl']),
],

install_requires = [
    "argcomplete >= 1.8.2",
    "colorama >= 0.3.7",
    "questionary >= 1.10.0",
    #"mputils @ file:///D:/mputils",
    "mputils @ git+https://github.com/saycv/mputils@dev#egg=mputils",
],

setup(
    name="padsprod",
    version=verstr,
    description="padsprod",
    long_description="Please visit `Github <https://github.com/saycv/padsprod>`_ for more information.",
    author="padsprod project developers",
    author_email="",
    url="https://github.com/saycv/padsprod",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    data_files=data_files,
    entry_points={"console_scripts": ["padsprod = padsprod.main:main"]},
    include_package_data=True,
    install_requires=install_requires,
)
