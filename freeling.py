# -*- coding: utf-8 -*-

import re
import subprocess
import threading
import queue
import xml.etree.cElementTree as etree
import sparv.util as util

SENTTAG = "s"
WORDTAG = "w"
END = b"27345327645267453684527685"


def freeling_wrapper(in_file, out_file, conf_file, lang, sent_end="Fp", slevel=""):
    """
    Read an XML or text document and process the text with FreeLing.
    - conf_file: path to a language specific FreeLing CFG file
    - lang: the two-letter language code of the language to be analyzed
    - sent_end: the POS tag that marks the end of a sentence
    - slevel: the sentence tag in the indata. Should only be set if the
      material already has sentence-level annotations
    """
    # Init FreeLing as child process
    fl_instance = Freeling(conf_file, lang, sent_end, slevel)

    # Parse document into tree
    try:
        tree = etree.parse(in_file)
        root = tree.getroot()
    except etree.ParseError:
        # Convert text document to XML
        f = open(in_file, 'r').read()
        text = '<text>\n' + f + '\n</text>'
        root = etree.fromstring(text)
        tree = etree.ElementTree(root)

    # Walk tree and send all text nodes to FreeLing
    if slevel:
        for node in root.iterfind(".//" + slevel):
            rawtext, _newsnode = prepare_node(fl_instance, node)
            run_freeling(fl_instance, node, rawtext)
    else:
        for node in treeiter(root):
            inputtext = " ".join(list(node.itertext())).encode(util.UTF8)
            rawtext, newsnode = prepare_node(fl_instance, node, inputtext)
            run_freeling(fl_instance, node, rawtext, newsnode=newsnode)

    # Kill running subprocess
    fl_instance.kill()

    # Write output file (usually in src directory)
    tree.write(out_file, encoding=util.UTF8)


class Freeling(object):
    """Handle the FreeLing process."""

    def __init__(self, conf_file, lang, sent_end, slevel):
        """Set variables and start FreeLing process."""
        self.conf_file = conf_file
        self.lang = lang
        self.sent_end = sent_end
        self.slevel = slevel
        self.start()
        self.error = False

    def start(self):
        """Start the external FreeLingTool."""
        self.process = subprocess.Popen(['analyze', '-f', self.conf_file, '--flush'],
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


def prepare_node(fl_instance, node, inputtext=""):
    """Extract input text for processing with FreeLing and clear node."""
    # Save the node's attributes before they are removed with node.clear()
    attrs = dict(node.attrib)

    if fl_instance.slevel:
        newsnode = None
        # Collect text from under this node and remove old text
        if node.text:
            rawtext = node.text.encode(util.UTF8)
            node.text = ""
        else:
            rawtext = b""
        # Collect text from children and remove them.
        for child in node.iter():
            if child.text or child.tail:
                rawtext += b" " + child.text.encode(util.UTF8) + b" " + child.tail.encode(util.UTF8)

    else:
        rawtext = inputtext
        newsnode = etree.Element(SENTTAG)

    # Remove contents from node (=flatten structure)
    node.clear()

    # Get back attributes that were removed with node.clear()
    for k, v in list(attrs.items()):
        node.set(k, v)

    return rawtext, newsnode


def run_freeling(fl_instance, node, rawtext, newsnode=None):
    """
    Send a chunk of material to FreeLing and get the analysis, using pipes.
    Do sentence segmentation unless slevel is set.
    """
    # Read stderr without blocking
    try:
        line = fl_instance.qerr.get(timeout=.1)
        util.log.warning("FreeLing error encountered: %s" % line)
        fl_instance.error = True
    except queue.Empty:
        # No errors, continue
        pass

    # Send material to FreeLing; Send blank lines for flushing;
    # Send end-marker to know when to stop reading stdout
    text = rawtext + b"\n" + END + b"\n"

    # Send input to FreeLing in thread (prevents blocking)
    threading.Thread(target=pump_input, args=[fl_instance.process.stdin, text]).start()

    # Read output line by line
    empty_output = 0
    for line in iter(fl_instance.process.stdout.readline, ''):

        if not line.strip():
            empty_output += 1
        else:
            empty_output = 0

        # Reached end marker, all text processed!
        if re.match(END, line):
            if fl_instance.slevel:
                break
            else:
                # Close the current sentence and attach to original node
                if len(list(newsnode)) > 0:
                    node.append(newsnode)
                break

        # No output recieved in a while. Skip this node and restart FreeLing.
        # Multiple blank lines in input are ignored by FreeLing.
        if empty_output > 5:
            if not fl_instance.error:
                util.log.warning("Something went wrong, FreeLing stopped responding.")
            make_fallback_output(node, rawtext)
            fl_instance.restart()
            return

        if len(line.rstrip()) > 0:
            newsnode = process_output(fl_instance, line, node, newsnode)


def process_output(fl_instance, line, node, newsnode):
    """Process one line of FreeLing's output and convert it to Sparv's XML format."""
    fields = line.split(b" ")

    if len(fields) >= 3:
        word = fields[0].decode(util.UTF8)
        lemma = fields[1].decode(util.UTF8)
        msd = fields[2].decode(util.UTF8)
        pos = util.msd_to_pos.convert(msd, fl_instance.lang)

        # Create new word node and add attributes
        newwnode = etree.Element(WORDTAG, {"pos": pos, "msd": msd, "lemma": lemma})
        newwnode.text = word

        # Attach new word node
        if fl_instance.slevel:
            node.append(newwnode)
        else:
            newsnode.append(newwnode)

            # If this ends a sentence, close <s>, attach, and create new <s>
            if msd == fl_instance.sent_end:
                if len(list(newsnode)) > 0:
                    node.append(newsnode)
                newsnode = etree.Element(SENTTAG)

    return newsnode


#####################
# Auxiliary functions
#####################

def treeiter(tree):
    """Tree generator that yields flattened nodes."""
    text = tree.text.strip() if tree.text else None
    if text:
        yield tree
    else:
        for child in tree:
            for i in treeiter(child):
                yield i


def enqueue_output(out, queue):
    """Auxiliary needed for reading without blocking."""
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()


def pump_input(pipe, lines):
    """Auxiliary for writing to pipe without blocking."""
    pipe.write(lines)
    # # If module stops working, maybe try splitting lines
    # for line in lines.split(b"\n"):
    #     pipe.write(line + b"\n")


def make_fallback_output(node, inputtext):
    """Create output without annotations in case FreeLing crashes for a sentence."""
    newsnode = etree.Element(SENTTAG)
    node.append(newsnode)
    words = inputtext.split()
    for w in words:
        newwnode = etree.Element(WORDTAG)
        newwnode.text = w.decode(util.UTF8)
        newsnode.append(newwnode)


if __name__ == "__main__":
    util.run.main(freeling_wrapper)
