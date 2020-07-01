"""Download FreeLing configs and make them available for Sparv."""

import subprocess

import sparv.util as util
from sparv import ModelOutput, modelbuilder


@modelbuilder("FreeLing config for Asturian", language=["ast"])
def get_ast_config(out: ModelOutput = ModelOutput("freeling/ast.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/as.cfg", out)


@modelbuilder("FreeLing config for Catalan", language=["cat"])
def get_cat_config(out: ModelOutput = ModelOutput("freeling/cat.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/ca.cfg", out)


@modelbuilder("FreeLing config for German", language=["deu"])
def get_deu_config(out: ModelOutput = ModelOutput("freeling/deu.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/de.cfg", out)


@modelbuilder("FreeLing config for English", language=["eng"])
def get_eng_config(out: ModelOutput = ModelOutput("freeling/eng.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/en.cfg", out)


@modelbuilder("FreeLing config for Spanish", language=["spa"])
def get_spa_config(out: ModelOutput = ModelOutput("freeling/spa.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/es.cfg", out)


@modelbuilder("FreeLing config for French", language=["fra"])
def get_fra_config(out: ModelOutput = ModelOutput("freeling/fra.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/fr.cfg", out)


@modelbuilder("FreeLing config for Galician", language=["glg"])
def get_glg_config(out: ModelOutput = ModelOutput("freeling/glg.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/gl.cfg", out)


@modelbuilder("FreeLing config for Italian", language=["ita"])
def get_ita_config(out: ModelOutput = ModelOutput("freeling/ita.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/it.cfg", out)


@modelbuilder("FreeLing config for Norwegian", language=["nob"])
def get_nob_config(out: ModelOutput = ModelOutput("freeling/nob.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/nb.cfg", out)


@modelbuilder("FreeLing config for Portuguese", language=["por"])
def get_por_config(out: ModelOutput = ModelOutput("freeling/por.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/pt.cfg", out)


@modelbuilder("FreeLing config for Russian", language=["rus"])
def get_rus_config(out: ModelOutput = ModelOutput("freeling/rus.cfg")):
    """Download FreeLing language config."""
    download("https://github.com/TALP-UPC/FreeLing/raw/4.1/data/config/ru.cfg", out)


@modelbuilder("FreeLing config for Slovenian", language=["slv"])
def get_slv_config(out: ModelOutput = ModelOutput("freeling/slv.cfg")):
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
