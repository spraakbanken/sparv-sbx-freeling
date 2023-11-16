"""Do analysis with FreeLing."""

import json
import os
import queue
import re
import signal
import subprocess
import threading
from typing import Optional

from sparv.api import Annotation, Binary, Config, Language, Model, Output, Text, annotator, get_logger, util
from sparv.api.util.tagsets import pos_to_upos
from sparv.api.util.tagsets.pos_to_upos import FALLBACK

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
             sentence_annotation: Optional[Annotation] = Annotation("[sbx_freeling.sentence_annotation]"),
             timeout: int = Config("sbx_freeling.timeout")):
    """Run FreeLing and output sentences, tokens, baseforms, upos and pos."""
    main(corpus_text, lang, conf_file, fl_binary, sentence_chunk, out_token, out_baseform, out_upos, out_pos,
         out_sentence, sentence_annotation, timeout)


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
                  sentence_annotation: Optional[Annotation] = Annotation("[sbx_freeling.sentence_annotation]"),
                  timeout: int = Config("sbx_freeling.timeout")):
    """Run FreeLing and output the usual annotations plus named entity types."""
    main(corpus_text, lang, conf_file, fl_binary, sentence_chunk, out_token, out_baseform, out_upos, out_pos,
         out_sentence, sentence_annotation, timeout, out_ne_type)


def main(corpus_text, lang, conf_file, fl_binary, sentence_chunk, out_token, out_baseform, out_upos, out_pos,
         out_sentence, sentence_annotation, timeout, out_ne_type=None):
    """Read an XML or text document and process the text with FreeLing."""
    # Init FreeLing as child process
    fl_instance = Freeling(fl_binary, conf_file.path, lang, sentence_annotation, timeout)

    text_data = corpus_text.read()
    sentence_segments = []
    all_tokens = []

    if sentence_annotation:
        # Go through all sentence spans and send text to FreeLing
        sentences_spans = sentence_annotation.read_spans()
        sentences_spans = list(sentences_spans)
        logger.progress(total=len(sentences_spans))
        for sentence_span in sentences_spans:
            inputtext = text_data[sentence_span[0]:sentence_span[1]]
            processed_output = run_freeling(fl_instance, inputtext, sentence_span[0])
            all_tokens.extend(processed_output)
            logger.progress()

    else:
        # Go through all text spans and send text to FreeLing
        text_spans = sentence_chunk.read_spans()
        text_spans = list(text_spans)
        logger.progress(total=len(text_spans))
        for text_span in text_spans:
            inputtext = text_data[text_span[0]:text_span[1]]
            processed_output = run_freeling(fl_instance, inputtext, text_span[0])
            for s in processed_output:
                all_tokens.extend(s)
                sentence_segments.append((s[0].start, s[-1].end))
                logger.progress()

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

    def __init__(self, fl_binary, conf_file, lang, sentence_annotation, timeout):
        """Set properties and start FreeLing process."""
        self.binary = util.system.find_binary(fl_binary)
        self.conf_file = conf_file
        self.lang = lang
        self.sentence_annotation = sentence_annotation
        self.start()
        self.error = False
        self.tagset = "Penn" if self.lang == "eng" else "EAGLES"
        self.timeout = timeout
        self.next_begin = 0  # FreeLing begin index of next output chunk (used as offset for calculating indexes)
        self.restarted = False  # Indicates whether FreeLing has been restarted while processing the current chunk

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
                                        bufsize=0, start_new_session=True)
        self.qerr = queue.Queue()
        self.terr = threading.Thread(target=enqueue_output, args=(self.process.stderr, self.qerr))
        self.terr.daemon = True  # thread dies with the program
        self.terr.start()

        self.qout = queue.Queue()
        self.tout = threading.Thread(target=enqueue_output, args=(self.process.stdout, self.qout))
        self.tout.daemon = True  # thread dies with the program
        self.tout.start()

    def kill(self):
        """Terminate current process."""
        # Freeling spawns children, so we need to kill the whole process group
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

    def restart(self):
        """Restart current process."""
        self.kill()
        self.start()
        self.restarted = True


def run_freeling(fl_instance, inputtext, input_start_index):
    """Send a chunk of material to FreeLing and get the analysis, using pipes."""
    # Read stderr without blocking
    try:
        line = fl_instance.qerr.get(timeout=.1)
        # Ignore the "No rule to get short version of tag" error (http://nlp.lsi.upc.edu/freeling/node/655)
        line = line.decode()
        if not line.startswith("TAGSET: No rule to get short version of tag"):
            logger.warning("FreeLing error encountered: %s", line)
            fl_instance.error = True
    except queue.Empty:
        # No errors, continue
        pass

    stripped_text = re.sub("\n", " ", inputtext)
    # logger.debug("Sending input to FreeLing:\n" + stripped_text)

    # Send material to FreeLing; Send blank lines for flushing; Send end-marker to know when to stop reading stdout
    text = stripped_text.encode(util.constants.UTF8) + b"\n" + END + b"\n"

    # Send input to FreeLing in thread (prevents blocking)
    threading.Thread(target=pump_input, args=[fl_instance.process.stdin, text]).start()
    # logger.debug("Done sending input to FreeLing!")

    return process_lines(fl_instance, stripped_text, input_start_index)


def process_lines(fl_instance, text, input_start_index):
    """Read and process FreeLing output line by line."""
    def make_empty_output():
        """Generate fake FreeLing output in case input could not be processed."""
        offset = fl_instance.next_begin
        tokens = []
        # Do dumb tokenisation: split on whitespace (but keep track of indexes)
        for token, (b, e) in [(m.group(0), (m.start(), m.end())) for m in re.finditer(r"\S+", text)]:
            t = {"begin": str(offset + b), "end": str(offset + e), "form": token, "lemma": token}
            tokens.append(t)
        # End position of the next token is irrelevant because next_begin will be reset to 0
        tokens.append({"form": END.decode(), "end": str(-1)})
        return [json.dumps({"sentences": [{"tokens": tokens}]})]

    processed_output = []
    empty_output = 0

    # Read stdout without blocking
    while True:
        try:
            line = fl_instance.qout.get(timeout=fl_instance.timeout)

            if not line.strip():
                empty_output += 1
            else:
                empty_output = 0
                processed_output.append(line.decode())
                # logger.debug("FreeLing output:\n" + line.decode().strip())

            # TODO: is this still needed?
            # No output recieved in a while. Skip this node and restart FreeLing.
            # (Multiple blank lines in input are ignored by FreeLing.)
            if empty_output > 5:
                if not fl_instance.error:
                    text_preview = text if len(text) <= 100 else text[:100] + "..."
                    logger.warning("Something went wrong, FreeLing stopped responding. If this happens frequently you "
                                   "could try increasing the 'sbx_freeling.timeout' config variable. The current input "
                                   f"chunk will not be analyzed properly: '{text_preview}'")
                fl_instance.restart()
                processed_output = make_empty_output()
                return process_json(fl_instance, processed_output, text, input_start_index)

            # Reached end marker, all text processed!
            if re.search(END, line):
                return process_json(fl_instance, processed_output, text, input_start_index)

        except queue.Empty:
            # Freeling has not responded within the timeout. Skip this node and restart FreeLing.
            text_preview = text if len(text) <= 100 else text[:100] + "..."
            logger.warning("Something went wrong, FreeLing stopped responding. If this happens frequently you "
                           "could try increasing the 'sbx_freeling.timeout' config variable. The current input "
                           f"chunk will not be analyzed properly: '{text_preview}'")
            fl_instance.restart()
            processed_output = make_empty_output()
            return process_json(fl_instance, processed_output, text, input_start_index)


def process_json(fl_instance, json_lines, inputtext, input_start_index):
    """Process json output from FreeLing into sentences and tokens."""
    # logger.debug(f"input_start_index: {input_start_index}; next_begin: {fl_instance.next_begin}")
    sentences = []
    current_sentence = []

    json_lines = "".join(json_lines)
    decoder = json.JSONDecoder()
    text = json_lines.lstrip()
    while text:
        obj, index = decoder.raw_decode(text)
        text = text[index:].lstrip()
        for sentence in obj.get("sentences", []):
            # logger.debug(sentence)

            if len(current_sentence):
                sentences.append(current_sentence)
                current_sentence = []

            for token in sentence.get("tokens", []):
                if token.get("form") == END.decode():
                    # Store the last end position of the chunk
                    fl_instance.next_begin = int(token.get("end")) + 1
                else:
                    current_sentence.append(make_token(fl_instance, token, inputtext, input_start_index))

    # If FreeLing has been restarted while processing this chunk reset next_begin
    if fl_instance.restarted:
        fl_instance.next_begin = 0
        fl_instance.restarted = False

    # Append last sentence
    if len(current_sentence):
        sentences.append(current_sentence)

    # In case of an existing sentence_annotation: flatten sentences list to a single sentence
    if fl_instance.sentence_annotation:
        return [t for s in sentences for t in s]
    else:
        # logger.debug(sentences)
        return sentences


def make_token(fl_instance, json_token, inputtext, input_start_index):
    """Process one FreeLing token and extract relevant information."""
    start = int(json_token.get("begin", -1)) - fl_instance.next_begin
    end = int(json_token.get("end", -1)) - fl_instance.next_begin
    word = inputtext[start:end]

    # logger.debug(f"word: '{word}', index: {start}-{end}, input: '{inputtext}'")
    # input_start_index: Index of the first char in this chunk (relative to the entire input text)
    start = input_start_index + start
    end = input_start_index + end

    baseform = json_token.get("lemma", "")
    pos = json_token.get("tag", "")
    upos = []
    if pos:
        for p in pos.split("+"):
            upos.append(pos_to_upos(p, fl_instance.lang, fl_instance.tagset))
    else:
        upos.append(FALLBACK)
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
