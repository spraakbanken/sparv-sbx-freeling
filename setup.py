"""Install script for the sparv-sbx-freeling plugin."""

import os.path

import setuptools


def get_readme(readme_path):
    """Get the contents of the README file."""
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, readme_path), encoding="utf-8") as f:
        return f.read()


setuptools.setup(
    name="sparv-sbx-freeling",
    version="5.2.0",
    description="FreeLing plug-in for Sparv (Språkbanken's corpus annotation pipeline)",
    long_description=get_readme("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/spraakbanken/sparv-sbx-freeling/",
    author="Språkbanken",
    author_email="sb-info@svenska.gu.se",
    license="GNU GPL",
    packages=["sbx_freeling"],
    python_requires=">=3.8",
    install_requires=["sparv-pipeline>=5.2.0"],
    entry_points={"sparv.plugin": ["sbx_freeling = sbx_freeling"]}
)
