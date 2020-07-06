"""Install script for the Sparv FreeLing plugin."""

import setuptools


setuptools.setup(
    name="sparv-freeling",
    version="4.0.dev0",
    description="FreeLing plug-in for Sparv (Språkbanken's corpus annotation pipeline)",
    url="https://github.com/spraakbanken/sparv-freeling/",
    author="Språkbanken",
    author_email="sb-info@svenska.gu.se",
    license="GNU GPL",
    packages=setuptools.find_packages(include=["freeling", "freeling.*"]),
    zip_safe=False,
    python_requires=">=3.6",
    # install_requires=["sparv-pipeline"],
    entry_points={"sparv.plugin": ["freeling = freeling"]}
)
