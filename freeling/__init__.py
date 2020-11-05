"""Annotations from FreeLing for various languages."""

from sparv import Config
from . import freeling, models

__config__ = [
    Config("freeling.binary", "analyze", description="FreeLing executable"),
    Config("freeling.conf", "freeling/[metadata.language].cfg", description="Path to FreeLing cfg file"),
    Config("freeling.sentence_chunk", "<text>",
           description="Text chunk (annotation) to use as input when segmenting sentences"),
    Config("freeling.sentence_annotation", "", description="Optional existing sentence segmentation annotation")
]
