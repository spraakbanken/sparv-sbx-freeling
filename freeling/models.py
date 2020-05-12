"""Download FreeLing configs and make them available for Sparv."""

import subprocess

import sparv.util as util
from sparv import ModelOutput, modelbuilder


@modelbuilder("FreeLing config for Asturian", optional=True)
def get_ast_config(out: str = ModelOutput("freeling/ast.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/as.cfg", out)


@modelbuilder("FreeLing config for Catalan", optional=True)
def get_cat_config(out: str = ModelOutput("freeling/cat.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/ca.cfg", out)


@modelbuilder("FreeLing config for German", optional=True)
def get_deu_config(out: str = ModelOutput("freeling/deu.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/de.cfg", out)


@modelbuilder("FreeLing config for English", optional=True)
def get_eng_config(out: str = ModelOutput("freeling/eng.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/en.cfg", out)


@modelbuilder("FreeLing config for Spanish", optional=True)
def get_spa_config(out: str = ModelOutput("freeling/spa.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/es.cfg", out)


@modelbuilder("FreeLing config for French", optional=True)
def get_fra_config(out: str = ModelOutput("freeling/fra.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/fr.cfg", out)


@modelbuilder("FreeLing config for Galician", optional=True)
def get_glg_config(out: str = ModelOutput("freeling/glg.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/gl.cfg", out)


@modelbuilder("FreeLing config for Italian", optional=True)
def get_ita_config(out: str = ModelOutput("freeling/ita.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/it.cfg", out)


@modelbuilder("FreeLing config for Norwegian", optional=True)
def get_nob_config(out: str = ModelOutput("freeling/nob.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/nb.cfg", out)


@modelbuilder("FreeLing config for Portuguese", optional=True)
def get_por_config(out: str = ModelOutput("freeling/por.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/pt.cfg", out)


@modelbuilder("FreeLing config for Russian", optional=True)
def get_rus_config(out: str = ModelOutput("freeling/rus.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/ru.cfg", out)


@modelbuilder("FreeLing config for Slovenian", optional=True)
def get_slv_config(out: str = ModelOutput("freeling/slv.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/sl.cfg", out)


################################################################################
# Auxiliaries
################################################################################


def download(url, out):
    """Download FreeLing config file after checking that the correct software is installed."""
    if check_installed():
        util.download_model(url, out)
    else:
        print("FreeLing software must be installed before config files can be downloaded.")


def check_installed():
    """Check if FreeLing Software is installed."""
    try:
        process = subprocess.run(["analyze"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.stderr.startswith(b"Configuration file not specified"):
            return True
        else:
            return False
    except FileNotFoundError:
        return False
