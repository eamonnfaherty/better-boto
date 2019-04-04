import setuptools
import os

with open(os.path.abspath(__file__).replace('setup.py', 'README.md'), "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="better-boto",
    version="0.6.6",
    author="Eamonn Faherty",
    author_email="python-packages@designandsolve.co.uk",
    description="Helpers to make using boto3 more enjoyable",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eamonnfaherty/better-boto",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "pyyaml>=4.2b1",
    ],
)
