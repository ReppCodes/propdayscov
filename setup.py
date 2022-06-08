import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="propdayscov",
    version="1.2.0",
    author="Andrew Repp",
    author_email="ajrepp1@gmail.com",
    description="A package for calculating medication PDC.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ReppCodes/propdayscov",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
) 