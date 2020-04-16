"""Do analysis with FreeLing."""

import logging
import queue
import re
import subprocess
import threading
from typing import Optional

import sparv.util as util
from sparv import Annotation, Config, Document, Language, Model, Output, annotator

log = logging.getLogger(__name__)


# Random token to signal end of input
END = b"27345327645267453684527685"


@annotator("Part-of-speech tags and baseforms from FreeLing")
def annotate(doc: str = Document,
             text: str = Annotation("<text>"),
             lang: str = Language,
             conf_file: str = Model("[freeling.conf=freeling/[language].cfg]"),
             out_token: str = Output("freeling.token", cls="token", description="Token segments"),
             out_word: str = Output("<token>:freeling.word", cls="token:word", description="Token strings"),
             out_baseform: str = Output("<token>:freeling.baseform", description="Baseforms from FreeLing"),
             out_pos: str = Output("<token>:freeling.pos", description="Part-of-speeches in UD"),
             out_msd: str = Output("<token>:freeling.msd", description="Part-of-speeches from FreeLing"),
             out_sentence: Optional[str] = Output("freeling.sentence", cls="sentence", description="Sentence segments"),
             slevel: str = Config("freeling.slevel", None)):
    """
    Read an XML or text document and process the text with FreeLing.

    - text: existing annotation with corpus text
    - sentence, token, word, lemma, pos, msd: annotations to be created
    - conf_file: path to a language specific FreeLing CFG file
    - lang: the two-letter language code of the language to be analyzed
    - slevel: the sentence tag in the indata. Should only be set if the
      material already has sentence-level annotations
    """
    # Init FreeLing as child process
    fl_instance = Freeling(conf_file, lang, slevel)

    corpus_text = util.read_corpus_text(doc)

    annotations = {
        "sentence_segments": [],
        "token_segments": [],
        "word_annotation": [],
        "pos_annotation": [],
        "msd_annotation": [],
        "baseform_annotation": []
    }

    # Go through all text elements and send text to FreeLing
    if slevel:
        sentences = util.read_annotation_spans(doc, slevel)
        for sentence_span in sentences:
            inputtext = corpus_text[sentence_span[0]:sentence_span[1]]
            processed_output = run_freeling(fl_instance, inputtext)
            process_sentence(processed_output, annotations, sentence_span[0], inputtext)

    else:
        text_spans = util.read_annotation_spans(doc, text)
        for text_span in text_spans:
            inputtext = corpus_text[text_span[0]:text_span[1]]
            processed_output = run_freeling(fl_instance, inputtext)
            # Go through output and try to match tokens with input text to get correct spans
            index_counter = text_span[0]
            for s in processed_output:
                index_counter, inputtext = process_sentence(s, annotations, index_counter, inputtext)

    # Write annotations
    util.write_annotation(doc, out_token, annotations["token_segments"])
    util.write_annotation(doc, out_word, annotations["word_annotation"])
    util.write_annotation(doc, out_pos, annotations["pos_annotation"])
    util.write_annotation(doc, out_msd, annotations["msd_annotation"])
    util.write_annotation(doc, out_baseform, annotations["baseform_annotation"])
    if not slevel:
        util.write_annotation(doc, out_sentence, annotations["sentence_segments"])

    # Kill running subprocess
    fl_instance.kill()


def process_sentence(sentence, annotations, index_counter, inputtext):
    """Extract and process annotations from sentence."""
    for token_annotation in sentence:
        match = re.match(r"\s*(%s)" % re.escape(token_annotation[1]), inputtext)
        if not match:
            match = re.match(r"\s*(%s)" % re.escape(re.sub("_", " ", token_annotation[1])), inputtext)
        # TODO: What if there is still no match??
        span = match.span(1)
        word_span = (span[0] + index_counter, span[1] + index_counter)
        annotations["token_segments"].append(word_span)
        annotations["word_annotation"].append(token_annotation[1])
        annotations["pos_annotation"].append(token_annotation[2])
        annotations["msd_annotation"].append(token_annotation[3])
        annotations["baseform_annotation"].append(token_annotation[4])
        # Forward inputtext
        inputtext = inputtext[span[1]:]
        index_counter += span[1]
        # Store word spans in token_annotation in order to be able to extract sentence spans later
        token_annotation[0] = word_span

    # Extract sentence span for current sentence
    annotations["sentence_segments"].append((sentence[0][0][0], sentence[-1][0][1]))

    return index_counter, inputtext


class Freeling(object):
    """Handle the FreeLing process."""

    def __init__(self, conf_file, lang, slevel):
        """Set properties and start FreeLing process."""
        self.conf_file = conf_file
        self.lang = lang
        self.slevel = slevel
        self.start()
        self.error = False

    def start(self):
        """Start the external FreeLingTool."""
        self.process = subprocess.Popen(["analyze", "-f", self.conf_file, "--flush"],
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
    """
    Send a chunk of material to FreeLing and get the analysis, using pipes.

    Do sentence segmentation unless fl_instance.slevel = True.
    """
    # Read stderr without blocking
    try:
        line = fl_instance.qerr.get(timeout=.1)
        log.error("FreeLing error encountered: %s", line)
        fl_instance.error = True
    except queue.Empty:
        # No errors, continue
        pass

    stripped_text = re.sub("\n", " ", inputtext)
    log.debug("Sending input to FreeLing:\n%s", stripped_text)

    # Send material to FreeLing; Send blank lines for flushing;
    # Send end-marker to know when to stop reading stdout
    text = stripped_text.encode(util.UTF8) + b"\n" + END + b"\n"

    # Send input to FreeLing in thread (prevents blocking)
    threading.Thread(target=pump_input, args=[fl_instance.process.stdin, text]).start()
    log.debug("Done sending input to FreeLing!")

    return process_fl_output(fl_instance, stripped_text)


def process_fl_output(fl_instance, text):
    """Read and process Freeling output line by line."""
    processed_output = []
    current_sentence = []
    empty_output = 0

    for line in iter(fl_instance.process.stdout.readline, ""):
        # print("FL out: %s" % line.decode("UTF-8"))

        # If this ends a sentence, attach sentence to output, and start a new (empty) sentence
        if not fl_instance.slevel and line == b"\n":
            if len(list(current_sentence)) > 0:
                processed_output.append(current_sentence)
            current_sentence = []

        # Many empty output lines probably mean that Freeling died
        if not line.strip():
            empty_output += 1
        else:
            empty_output = 0
            log.debug("FreeLing output:\n%s", line.strip())

        # No output recieved in a while. Skip this node and restart FreeLing.
        # Multiple blank lines in input are ignored by FreeLing.
        if empty_output > 5:
            if not fl_instance.error:
                log.error("Something went wrong, FreeLing stopped responding.")
            processed_output.append(make_fallback_output(text))
            fl_instance.restart()
            return

        # Reached end marker, all text processed!
        if re.match(END, line):
            if fl_instance.slevel:
                return current_sentence
            else:
                # Add current_sentence to processed_output
                if len(current_sentence) > 0:
                    processed_output.append(current_sentence)
                return processed_output

        # Freeling returned some output, process it
        if len(line.rstrip()) > 0:
            current_sentence.append(make_token(fl_instance, line))


def make_token(fl_instance, line):
    """Process one line of FreeLing's output and extract relevant information."""
    fields = line.decode(util.UTF8).split(" ")

    if len(fields) >= 3:
        # Create new word with attributes
        token = fields[0]
        lemma = fields[1]
        msd = fields[2]
        pos = util.msd_to_pos.convert(msd, fl_instance.lang)
        return [(), token, pos, msd, lemma]

    else:
        return [(), line.decode(util.UTF8), "", "", ""]


#####################
# Auxiliary functions
#####################

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


def make_fallback_output(inputtext):
    """Create output without annotations in case FreeLing crashes for a sentence."""
    sentence = []
    words = inputtext.split()
    for w in words:
        sentence.append([(), w.decode(util.UTF8), "", "", ""])
    return sentence
