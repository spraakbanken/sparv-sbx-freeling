"""Install script for the Sparv FreeLing plugin."""

import os.path

import setuptools


def get_readme(readme_path):
    """Get the contents of the README file."""
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, readme_path), encoding="utf-8") as f:
        return f.read()


setuptools.setup(
    name="sparv-freeling",
    version="4.0",
    description="FreeLing plug-in for Sparv (Språkbanken's corpus annotation pipeline)",
    long_description=get_readme("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/spraakbanken/sparv-freeling/",
    author="Språkbanken",
    author_email="sb-info@svenska.gu.se",
    license="GNU GPL",
    packages=["freeling"],
    python_requires=">=3.6",
    # install_requires=["sparv-pipeline@https://github.com/spraakbanken/sparv-pipeline/archive/v4.tar.gz"], # https://www.python.org/dev/peps/pep-0508/
    entry_points={"sparv.plugin": ["freeling = freeling"]}
)
