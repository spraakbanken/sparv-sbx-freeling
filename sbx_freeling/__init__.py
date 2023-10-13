"""Annotations from FreeLing for various languages."""

from sparv.api import Config
from . import freeling, models

__config__ = [
    Config("sbx_freeling.binary", "analyze", description="FreeLing executable"),
    Config("sbx_freeling.conf", "sbx_freeling/[metadata.language].cfg", description="Path to FreeLing cfg file"),
    Config("sbx_freeling.sentence_chunk", "<text>",
           description="Text chunk (annotation) to use as input when segmenting sentences"),
    Config("sbx_freeling.sentence_annotation", "", description="Optional existing sentence segmentation annotation"),
    Config("sbx_freeling.timeout", 300, datatype=int,
           description="Timeout (in seconds) after which to kill FreeLing if it does not respond")
]
