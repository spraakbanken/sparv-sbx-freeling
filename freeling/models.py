"""Download FreeLing configs and make them available for Sparv."""

import sparv.util as util
from sparv import Binary, ModelOutput, modelbuilder


CONFIG_URL = "https://github.com/TALP-UPC/FreeLing/raw/4.2/data/config/"


@modelbuilder("FreeLing config for Asturian", language=["ast"])
def get_ast_config(out: ModelOutput = ModelOutput("freeling/ast.cfg"),
                   fl_binary: Binary = Binary("[freeling.binary]")):
    """Download FreeLing language config."""
    download(CONFIG_URL + "as.cfg", out, fl_binary)


@modelbuilder("FreeLing config for Catalan", language=["cat"])
def get_cat_config(out: ModelOutput = ModelOutput("freeling/cat.cfg"),
                   fl_binary: Binary = Binary("[freeling.binary]")):
    """Download FreeLing language config."""
    download(CONFIG_URL + "ca.cfg", out, fl_binary)


@modelbuilder("FreeLing config for German", language=["deu"])
def get_deu_config(out: ModelOutput = ModelOutput("freeling/deu.cfg"),
                   fl_binary: Binary = Binary("[freeling.binary]")):
    """Download FreeLing language config."""
    download(CONFIG_URL + "de.cfg", out, fl_binary)


@modelbuilder("FreeLing config for English", language=["eng"])
def get_eng_config(out: ModelOutput = ModelOutput("freeling/eng.cfg"),
                   fl_binary: Binary = Binary("[freeling.binary]")):
    """Download FreeLing language config."""
    download(CONFIG_URL + "en.cfg", out, fl_binary)


@modelbuilder("FreeLing config for Spanish", language=["spa"])
def get_spa_config(out: ModelOutput = ModelOutput("freeling/spa.cfg"),
                   fl_binary: Binary = Binary("[freeling.binary]")):
    """Download FreeLing language config."""
    download(CONFIG_URL + "es.cfg", out, fl_binary)


@modelbuilder("FreeLing config for French", language=["fra"])
def get_fra_config(out: ModelOutput = ModelOutput("freeling/fra.cfg"),
                   fl_binary: Binary = Binary("[freeling.binary]")):
    """Download FreeLing language config."""
    download(CONFIG_URL + "fr.cfg", out, fl_binary)


@modelbuilder("FreeLing config for Galician", language=["glg"])
def get_glg_config(out: ModelOutput = ModelOutput("freeling/glg.cfg"),
                   fl_binary: Binary = Binary("[freeling.binary]")):
    """Download FreeLing language config."""
    download(CONFIG_URL + "gl.cfg", out, fl_binary)


@modelbuilder("FreeLing config for Italian", language=["ita"])
def get_ita_config(out: ModelOutput = ModelOutput("freeling/ita.cfg"),
                   fl_binary: Binary = Binary("[freeling.binary]")):
    """Download FreeLing language config."""
    download(CONFIG_URL + "it.cfg", out, fl_binary)


@modelbuilder("FreeLing config for Norwegian", language=["nob"])
def get_nob_config(out: ModelOutput = ModelOutput("freeling/nob.cfg"),
                   fl_binary: Binary = Binary("[freeling.binary]")):
    """Download FreeLing language config."""
    download(CONFIG_URL + "nb.cfg", out, fl_binary)


@modelbuilder("FreeLing config for Portuguese", language=["por"])
def get_por_config(out: ModelOutput = ModelOutput("freeling/por.cfg"),
                   fl_binary: Binary = Binary("[freeling.binary]")):
    """Download FreeLing language config."""
    download(CONFIG_URL + "pt.cfg", out, fl_binary)


@modelbuilder("FreeLing config for Russian", language=["rus"])
def get_rus_config(out: ModelOutput = ModelOutput("freeling/rus.cfg"),
                   fl_binary: Binary = Binary("[freeling.binary]")):
    """Download FreeLing language config."""
    download(CONFIG_URL + "ru.cfg", out, fl_binary)


@modelbuilder("FreeLing config for Slovenian", language=["slv"])
def get_slv_config(out: ModelOutput = ModelOutput("freeling/slv.cfg"),
                   fl_binary: Binary = Binary("[freeling.binary]")):
    """Download FreeLing language config."""
    download(CONFIG_URL + "sl.cfg", out, fl_binary)


################################################################################
# Auxiliaries
################################################################################


def download(url, out, fl_binary):
    """Download FreeLing config file after checking that the correct software is installed."""
    if util.find_binary(fl_binary):
        out.download(url)
    else:
        print("FreeLing software must be installed before config files can be downloaded.")
