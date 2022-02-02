import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pysolarmanv5",
    version="2.3.0",
    author="Jonathan McCrohan",
    author_email="jmccrohan@gmail.com",
    description=(
        "A Python library for interacting with Solarman (IGEN-Tech) "
        "v5 based Solar Data Loggers"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="BSD",
    keywords="solarman igen-tech modbus solar inverter",
    url="https://github.com/jmccrohan/pysolarmanv5",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "umodbus",
    ],
)
