from setuptools import setup, find_packages

setup(
    name="WizPub",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "requests",
        "markdown"
    ],
    entry_points='''
        [console_scripts]
        wizpub=wizpublishtool.wizpub:wizpub
    ''',
)
