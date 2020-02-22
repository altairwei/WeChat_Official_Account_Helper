from setuptools import setup, find_packages

from docpub import __version__

setup(
    name="docpub",
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "requests",
        "markdown",
        "confuse"
    ],
    entry_points='''
        [console_scripts]
        docpub=docpub.cli:cli
    ''',
)
