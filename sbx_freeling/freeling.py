"""Do analysis with FreeLing."""

import json
import queue
import re
import subprocess
import threading
from typing import Optional

from sparv.api import Annotation, Binary, Language, Model, Output, Text, annotator, get_logger, util
from sparv.api.util.tagsets import pos_to_upos

logger = get_logger(__name__)


# Random token to signal end of input
END = b"27345327645267453684527685"

# Languages supporting Named entity classification ("--nec" and "--ner" flags)
NEC_LANGS = ["cat", "eng", "spa", "por"]


@annotator("POS tags and baseforms from FreeLing", language=["ast", "fra", "glg", "ita", "nob", "rus", "slv"])
def annotate(corpus_text: Text = Text(),
             lang: Language = Language,
             conf_file: Model = Model("[sbx_freeling.conf]"),
             fl_binary: Binary = Binary("[sbx_freeling.binary]"),
             sentence_chunk: Optional[Annotation] = Annotation("[sbx_freeling.sentence_chunk]"),
             out_token: Output = Output("sbx_freeling.token", cls="token", description="Token segments"),
             out_baseform: Output = Output("<token>:sbx_freeling.baseform", description="Baseforms from FreeLing"),
             out_upos: Output = Output("<token>:sbx_freeling.upos", cls="token:upos", description="Part-of-speeches in UD"),
             out_pos: Output = Output("<token>:sbx_freeling.pos", cls="token:pos",
                                      description="Part-of-speeches from FreeLing"),
             out_sentence: Optional[Output] = Output("sbx_freeling.sentence", cls="sentence", description="Sentence segments"),
             sentence_annotation: Optional[Annotation] = Annotation("[sbx_freeling.sentence_annotation]")):
    """Run FreeLing and output sentences, tokens, baseforms, upos and pos."""
    main(corpus_text, lang, conf_file, fl_binary, sentence_chunk, out_token, out_baseform, out_upos, out_pos,
         out_sentence, sentence_annotation)


@annotator("POS tags, baseforms and named entities from FreeLing", language=["cat", "deu", "eng", "spa", "por"])
def annotate_full(corpus_text: Text = Text(),
                  lang: Language = Language(),
                  conf_file: Model = Model("[sbx_freeling.conf]"),
                  fl_binary: Binary = Binary("[sbx_freeling.binary]"),
                  sentence_chunk: Optional[Annotation] = Annotation("[sbx_freeling.sentence_chunk]"),
                  out_token: Output = Output("sbx_freeling.token", cls="token", description="Token segments"),
                  out_baseform: Output = Output("<token>:sbx_freeling.baseform", description="Baseforms from FreeLing"),
                  out_upos: Output = Output("<token>:sbx_freeling.upos", cls="token:upos",
                                            description="Part-of-speeches in UD"),
                  out_pos: Output = Output("<token>:sbx_freeling.pos", cls="token:pos",
                                           description="Part-of-speeches from FreeLing"),
                  out_ne_type: Output = Output("<token>:sbx_freeling.ne_type", cls="token:named_entity_type",
                                               description="Named entitiy types from FreeLing"),
                  out_sentence: Optional[Output] = Output("sbx_freeling.sentence", cls="sentence",
                                                          description="Sentence segments"),
                  sentence_annotation: Optional[Annotation] = Annotation("[sbx_freeling.sentence_annotation]")):
    """Run FreeLing and output the usual annotations plus named entity types."""
    main(corpus_text, lang, conf_file, fl_binary, sentence_chunk, out_token, out_baseform, out_upos, out_pos,
         out_sentence, sentence_annotation, out_ne_type)


def main(corpus_text, lang, conf_file, fl_binary, sentence_chunk, out_token, out_baseform, out_upos, out_pos,
         out_sentence, sentence_annotation, out_ne_type=None):
    """Read an XML or text document and process the text with FreeLing."""
    # Init FreeLing as child process
    fl_instance = Freeling(fl_binary, conf_file.path, lang, sentence_annotation)

    text_data = corpus_text.read()
    sentence_segments = []
    all_tokens = []
    last_position = 0

    if sentence_annotation:
        # Go through all sentence spans and send text to FreeLing
        sentences_spans = sentence_annotation.read_spans()
        for sentence_span in sentences_spans:
            inputtext = text_data[sentence_span[0]:sentence_span[1]]
            freeling_output = run_freeling(fl_instance, inputtext)
            processed_output, last_position = process_json(
                fl_instance, freeling_output, inputtext, sentence_span[0], last_position)
            all_tokens.extend(processed_output)

    else:
        # Go through all text spans and send text to FreeLing
        text_spans = sentence_chunk.read_spans()
        for text_span in text_spans:
            inputtext = text_data[text_span[0]:text_span[1]]
            freeling_output = run_freeling(fl_instance, inputtext)
            processed_output, last_position = process_json(
                fl_instance, freeling_output, inputtext, text_span[0], last_position)
            for s in processed_output:
                all_tokens.extend(s)
                sentence_segments.append((s[0].start, s[-1].end))

    # Write annotations
    if all_tokens:
        out_token.write([(t.start, t.end) for t in all_tokens])
        out_upos.write([t.upos for t in all_tokens])
        out_pos.write([t.pos for t in all_tokens])
        out_baseform.write([t.baseform for t in all_tokens])
    if out_ne_type:
        out_ne_type.write([t.name_type for t in all_tokens])
    # TODO: Sparv does not support optional outputs yet, so always write out_sentence, even if it's empty
    out_sentence.write(sentence_segments)

    # Kill running subprocess
    fl_instance.kill()


class Freeling:
    """Handle the FreeLing process."""

    def __init__(self, fl_binary, conf_file, lang, sentence_annotation):
        """Set properties and start FreeLing process."""
        self.binary = util.system.find_binary(fl_binary)
        self.conf_file = conf_file
        self.lang = lang
        self.sentence_annotation = sentence_annotation
        self.start()
        self.error = False
        self.tagset = "Penn" if self.lang == "eng" else "EAGLES"

    def start(self):
        """Start the external FreeLingTool."""
        ne_flags = []
        # Do named entitiy recognition and classification if supported for language
        if self.lang in NEC_LANGS:
            ne_flags = ["--ner", "--nec"]
        # Flags --nortkcon --nortk prevent FreeLing from splitting contractions
        self.process = subprocess.Popen([self.binary, *ne_flags, "--outlv tagged", "--output json",
                                         "--nortkcon", "--nortk", "-f", self.conf_file, "--flush"],
                                        stdout=subprocess.PIPE,
                                        stdin=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        bufsize=0)
        self.qerr = queue.Queue()
        self.terr = threading.Thread(target=enqueue_output, args=(self.process.stderr, self.qerr))
        self.terr.daemon = True  # thread dies with the program
        self.terr.start()

    def kill(self):
        """Terminate current process."""
        util.system.kill_process(self.process)

    def restart(self):
        """Restart current process."""
        self.kill()
        self.start()


def run_freeling(fl_instance, inputtext):
    """Send a chunk of material to FreeLing and get the analysis, using pipes."""
    # Read stderr without blocking
    try:
        line = fl_instance.qerr.get(timeout=.1)
        # Ignore the "No rule to get short version of tag" error (http://nlp.lsi.upc.edu/freeling/node/655)
        line = line.decode()
        if not line.startswith("TAGSET: No rule to get short version of tag"):
            logger.error("FreeLing error encountered: %s", line)
            fl_instance.error = True
    except queue.Empty:
        # No errors, continue
        pass

    stripped_text = re.sub("\n", " ", inputtext)
    # logger.debug("Sending input to FreeLing:\n" + stripped_text)

    # Send material to FreeLing; Send blank lines for flushing;
    # Send end-marker to know when to stop reading stdout
    text = stripped_text.encode(util.constants.UTF8) + b"\n" + END + b"\n"

    # Send input to FreeLing in thread (prevents blocking)
    threading.Thread(target=pump_input, args=[fl_instance.process.stdin, text]).start()
    logger.debug("Done sending input to FreeLing!")

    return process_lines(fl_instance, stripped_text)


def process_lines(fl_instance, text):
    """Read and process Freeling output line by line."""
    processed_output = []
    empty_output = 0

    for line in iter(fl_instance.process.stdout.readline, ""):
        # Many empty output lines probably mean that Freeling died
        if not line.strip():
            empty_output += 1
        else:
            empty_output = 0
            processed_output.append(line.decode())
            logger.debug("FreeLing output:\n" + line.decode().strip())

        # No output recieved in a while. Skip this node and restart FreeLing.
        # (Multiple blank lines in input are ignored by FreeLing.)
        if empty_output > 5:
            if not fl_instance.error:
                logger.error("Something went wrong, FreeLing stopped responding.")
            fl_instance.restart()
            return []

        # Reached end marker, all text processed!
        if re.search(END, line):
            return processed_output


def process_json(fl_instance, json_lines, inputtext, start_pos, last_position):
    """Process json output from FreeLing into sentences and tokens."""
    sentences = []
    current_sentence = []

    json_lines = "".join(json_lines)
    decoder = json.JSONDecoder()
    text = json_lines.lstrip()
    while text:
        obj, index = decoder.raw_decode(text)
        text = text[index:].lstrip()
        for sentence in obj.get("sentences", []):

            if len(current_sentence):
                sentences.append(current_sentence)
                current_sentence = []

            for token in sentence.get("tokens", []):
                if token.get("form") == END.decode():
                    # Store the last end position of the chunk
                    last_position = int(token.get("end")) + 1
                else:
                    current_sentence.append(make_token(fl_instance, token, inputtext, start_pos, last_position))

    # Append last sentence
    if len(current_sentence):
        sentences.append(current_sentence)

    # In case of an existing sentence_annotation: flatten sentences list to a single sentence
    if fl_instance.sentence_annotation:
        return [t for s in sentences for t in s], last_position
    else:
        return sentences, last_position


def make_token(fl_instance, json_token, inputtext, start_pos, last_position):
    """Process one FreeLing token and extract relevant information."""
    start = int(json_token.get("begin", -1)) - last_position
    end = int(json_token.get("end", -1)) - last_position
    word = inputtext[start:end]

    start = start_pos + start
    end = start_pos + end
    # logger.debug(f"\n{inputtext}\n{word} {start}-{end}")

    baseform = json_token.get("lemma", "")
    pos = json_token.get("tag", "")
    upos = []
    for p in pos.split("+"):
        upos.append(pos_to_upos(p, fl_instance.lang, fl_instance.tagset))
    upos = "+".join(upos)
    name_type = json_token.get("neclass", "")

    return Token(word, pos, upos, baseform, name_type, start, end)


################################################################################
# Auxiliaries
################################################################################

class Token:
    """Object to store annotation information for a token."""

    def __init__(self, word, pos, upos, baseform, name_type="", start=-1, end=-1):
        """Set attributes."""
        self.word = word
        self.pos = pos
        self.upos = upos
        self.baseform = baseform
        self.name_type = name_type
        self.start = start
        self.end = end

    def __repr__(self):
        return f"{self.word} <{self.baseform} {self.pos} {self.upos} {self.name_type}> ({self.start}-{self.end})"


def enqueue_output(out, queue):
    """Auxiliary needed for reading without blocking."""
    for line in iter(out.readline, b""):
        queue.put(line)
    out.close()


def pump_input(pipe, lines):
    """Auxiliary for writing to pipe without blocking."""
    pipe.write(lines)
    # # If module stops working, maybe try splitting lines
    # for line in lines.split(b"\n"):
    #     pipe.write(line + b"\n")
