# sparv-freeling

This is a plugin for the [Sparv pipeline](https://github.com/spraakbanken/sparv-pipeline) 
containing a wrapper for [FreeLing](http://nlp.lsi.upc.edu/freeling/node/30).
Please observe that this plugin has a more restrictive license than the Sparv piepeline!

This plugin allows you to run the Sparv pipeline and get sentence segmentation, tokenisation, baseform analysis, 
and part-of-speech annotations for the following languages:

* Asturian
* Catalan
* English
* French
* Galician
* German
* Italian
* Norwegian
* Portuguese
* Russian
* Slovenian
* Spanish

Furthermore Sparv will convert the FreeLing POS-tags into [Universal POS tags](https://universaldependencies.org/u/pos/)
and output them as a separate annotation.

Some of these languages (Catalan, English, German, Portuguese and Spanish) also support named-entity recognition.

## Prerequisites

* [Sparv pipeline](https://github.com/spraakbanken/sparv-pipeline)
* [FreeLing 4.1](https://github.com/TALP-UPC/FreeLing/releases/tag/4.1)
* [Python 3.6](http://python.org/) or newer
* [pip](https://pip.pypa.io/en/stable/installing)


## Installation

1. Download the sparv-freeling repository:

    `git clone git@github.com:spraakbanken/sparv-freeling.git`

2. Install the sparv-freeling plugin with pipx:

    `pipx inject sparv-pipeline ./sparv-freeling`

## Usage

The Sparv pipeline needs a config file describing your corpus and the desired output format.

Example corpus (`original/myfile.xml`):

```
<text title="Example">
  This is an example for how to run Sparv.
</text>
```

Example config file (`config.yaml`):

TODO!

Example folder structure:

```
mycorpus/
    config.yaml
    original/
        myfile.xml
```


Command for creating xml with annotations:

    sparv run

Result file (`export/xml/myfile_export.xml`):
```
<?xml version="1.0" encoding="UTF-8"?>
<text lix="20.00" title="Example">
  <sentence>
    <token baseform="this" ne_type="" pos="DT" upos="DET">This</token>
    <token baseform="be" ne_type="" pos="VBZ" upos="VERB">is</token>
    <token baseform="a" ne_type="" pos="DT" upos="DET">an</token>
    <token baseform="example" ne_type="" pos="NN" upos="NOUN">example</token>
    <token baseform="for" ne_type="" pos="IN" upos="ADP">for</token>
    <token baseform="how" ne_type="" pos="WRB" upos="ADV">how</token>
    <token baseform="to" ne_type="" pos="TO" upos="PART">to</token>
    <token baseform="run" ne_type="" pos="VB" upos="VERB">run</token>
    <token baseform="sparv" ne_type="person" pos="NP00SP0" upos="PROPN">Sparv</token>
    <token baseform="." ne_type="" pos="Fp" upos="PUNCT">.</token>
  </sentence>
</text>
```


# Additional Info about Annotations

A full list of what analyses are supported for what languages can be found here:

https://freeling-user-manual.readthedocs.io/en/latest/basics/#supported-languages

## Integrating dependency parsing

FreeLing supports dependency parsing for some languages. The output format is a bit cumbersome though.

Input:
`This is a sentence.`

Output:
`DT/top/(This this DT -) [
  vb-be/modnorule/(is be VBZ -)
  sn-chunk/modnorule/(sentence sentence NN -) [
    DT/det/(a a DT -)
  ]
  st-brk/modnorule/(. . Fp -)
]`

It is possible to write a new parser to handle this format but so far this has not been a priority for us.
