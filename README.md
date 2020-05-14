# sparv-freeling

Extension for Sparv containing a wrapper for [FreeLing](http://nlp.lsi.upc.edu/freeling/node/30).
This allows you to run the Sparv pipeline and get segmentation, lemmas,
and part-of-speech annotations for the following languages:

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


## Installation

* Download and install the [Sparv pipeline](https://github.com/spraakbanken/sparv-pipeline).
* Download and install [FreeLing 4.1](https://github.com/TALP-UPC/FreeLing/releases/tag/4.1).
* Copy the `freeling` directory into the `sparv/modules` directory of your Sparv installation.

## Usage

The Sparv pipeline is run by executing a Makefile for a given corpus.

Example corpus (`mycorpus.xml`):

```
<text title="Example">
  This is an example for how to run Sparv.
</text>
```

Example Makefile:
```
include $(SPARV_MAKEFILES)/Makefile.config
corpus = example
lang = en
analysis = fl

vrt_columns_annotations = word pos msd baseform
vrt_columns             = word pos msd lemma   

vrt_structs_annotations = sentence.id text text.title
vrt_structs             = sentence:id text text:title

xml_elements    = text text:title s        w     w:pos     w:msd     w:lemma       
xml_annotations = text text.title sentence token token.pos token.msd token.baseform

include $(SPARV_MAKEFILES)/Makefile.rules
```

Example folder structure:

```
mycorpus/
    Makefile
    original/
        xml/
            mycorpus.xml
```


Command for creating xml with annotations:

    make export mycorpus

Result file (`export.original/mycorpus.xml`):
```
<corpus>
  <text title="Example">
    <sentence id="enc022-enc5ca">
      <w pos="DET" msd="DT" lemma="this">This</w>
      <w pos="VERB" msd="VBZ" lemma="be">is</w>
      <w pos="DET" msd="DT" lemma="a">an</w>
      <w pos="NOUN" msd="NN" lemma="example">example</w>
      <w pos="ADP" msd="IN" lemma="for">for</w>
      <w pos="ADV" msd="WRB" lemma="how">how</w>
      <w pos="PART" msd="TO" lemma="to">to</w>
      <w pos="VERB" msd="VB" lemma="run">run</w>
      <w pos="PROPN" msd="NP" lemma="sparv">Sparv</w>
      <w pos="PUNCT" msd="Fp" lemma=".">.</w>
    </sentence>
  </text>
</corpus>
```


# Additional Info about Annotations

This Sparv extension provides support for sentence segmentation, tokenisation, baseform analysis and POS-tagging for 12 different languages. Furthermore the Sparv converts the POS-tags into [Universal POS tags](https://universaldependencies.org/u/pos/) and outputs them as a separate entity. The extension can also ouput named entitiy types for five of these languages. A full list of what analyses are supported for what languages can be found here:

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
