import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="gl-query",
    version="0.0.0",
    description="Query GitLab API for useful project and pipeline information.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/jay-jain/gl-query",
    author="Jay Jain",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["gl_query"],
    include_package_data=True,
    install_requires=["requests", "prettytable"],
    entry_points={
        "console_scripts": [
            "gl-query=gl_query.query:main",
        ]
    }
)

version = {}
with open("gl_query/__init__.py") as fp:
    exec(fp.read(), version)