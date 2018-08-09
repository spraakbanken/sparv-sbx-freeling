# -*- coding: utf-8 -*-

# TODO: After switching to Python 3, this can be rewritten using the
# Python bindings for FL instead of subprocess/piping.

import re
from queue import Queue, Empty
from threading import Thread
import xml.etree.cElementTree as ET
import subprocess
import sparv.util as util

SENTTAG = "s"
WORDTAG = "w"

# Sufficiently random material that FreeLing will always treat as one
# token. It signals to the sender that begin/end of processed data has
# been reached in the output.
START = b"27345327645267453684527684"
END   = b"27345327645267453684527685"


def fl_proc(in_file, out_file, conf_file, lang, sent_end="Fp", slevel=""):
    """ Read an XML or text document and process the text with FreeLing.
    Works for English, French, German, Italian, Portuguese, Russian, Spanish.
    - conf_file is a language specific FreeLing CFG file
    - lang is the two-letter language code of the language to be analyzed
    - sent_end is the tag that marks the end of a sentence
    - slevel should be set if the material already has sentence-level annotations
    """
    # Init the external FreeLingTool
    fl = Freeling(conf_file)

    # Parse document into tree
    try:
        tree = ET.parse(in_file)
        root = tree.getroot()

    # Convert text document to XML
    except ET.XMLSyntaxError:
        f = open(in_file, 'r').read()
        text = '<text>\n' + f + '\n</text>'
        root = ET.fromstring(text)
        tree = ET.ElementTree(root)

    # Iterate through tree and FreeLingize all text nodes
    if slevel:
        for node in root.iterfind(".//" + slevel):
            fl_exec(fl, node, "", lang, sent_end, slevel)
    else:
        for node in treeiter(root):
            inputtext = " ".join(list(node.itertext())).encode(util.UTF8)
            fl_exec(fl, node, inputtext, lang, sent_end, slevel)

    # Kill running subprocess
    fl.kill()
    # util.system.kill_process(fl)

    # Write file
    tree.write(out_file, encoding=util.UTF8)


def treeiter(tree):
    """Tree generator that yields flattened nodes. """
    text = tree.text.strip() if tree.text else None
    if text:
        yield tree
    else:
        for child in tree:
            for i in treeiter(child):
                yield i


class Freeling(object):
    """Handles Freeling-processes."""
    def __init__(self, config_file):
        self.config_file = config_file
        self.start()
        self.error = False

    def start(self):
        """Start the external FreeLingTool."""
        self.process = subprocess.Popen(['analyze', '-f', self.config_file, "--flush"],
                                        stdout=subprocess.PIPE,
                                        stdin=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        bufsize=0)
        self.queue = Queue()
        t = Thread(target=enqueue_output, args=(self.process.stderr, self.queue))
        t.daemon = True  # thread dies with the program
        t.start()

    def kill(self):
        util.system.kill_process(self.process)

    def restart(self):
        self.kill()
        self.start()


def fl_exec(fl_instance, node, inputtext, lang, sent_end, slevel):
    """Function that sends one chunk of material to FreeLing and gets the
    analysis back, using pipes. Does sentence segmentation unless slevel is set."""
    fl = fl_instance.process

    # Save this node's attributes before they are removed with clear()
    attrs = dict(node.attrib)

    if slevel:
        # Collect stuff from under this node and remove old text.
        if node.text:
            rawtext = node.text.encode(util.UTF8)
            node.text = ""
        else:
            rawtext = b""
        # Collect text from children and remove them.
        for child in node.iter():
            if child.text or child.tail:
                rawtext += b" " + child.text.encode(util.UTF8) + b" " + child.tail.encode(util.UTF8)
        node.clear()

    else:
        # Collect stuff from under this node and remove contents. (=flatten structure)
        attrs = dict(node.attrib)
        node.clear()
        rawtext = inputtext

        # We assume that at this stage, all sentences are within XML tags.
        # Hence, we start a new <s> for each existing block of text sent to FL.
        newsnode = ET.Element(SENTTAG)

    # Get back attributes that were lost in node.clear()
    for k, v in list(attrs.items()):
        node.set(k, v)

    # Send material with begin/end markers to FreeLing via pipe.
    fl.stdin.write(START + b'\n' + rawtext + b'\n' + END + b'\n')

    # Read stderr without blocking
    try:
        line = fl_instance.queue.get(timeout=.1)
        util.log.warning("Freeling error encountered: %s" % line)
        fl_instance.error = True
    except Empty:
        pass

    # Forward to the BEGIN marker.
    readin = b""
    while not re.match(START, readin):
        readin = fl.stdout.readline()

    n = 0
    # Read everything until the END marker occurs.
    while True:
        readin = fl.stdout.readline()
        if not readin.strip():
            n += 1
            # If there is no output and and error has occurred
            # skip this node and restart freeling
            if n == 10 and fl_instance.error:
                make_fallback_output(node, rawtext)
                fl_instance.restart()
                return
        if re.match(END, readin):
            fl_instance.error = False
            if slevel:
                break
            else:
                # Close the current sentence and attach to original
                # annotation node (usually <link>).
                if len(list(newsnode)) > 0:
                    node.append(newsnode)
                break

        if len(readin) > 0:
            # ... and process it. We only need the first three fields.
            fields = readin.split(b" ")
            if len(fields) >= 3:

                # Add stuff as XML nodes
                # Create new node.
                msd = fields[2].decode(util.UTF8)
                pos = util.msd_to_pos.convert(msd, lang)

                newnode = ET.Element(WORDTAG, {"pos": pos, "msd": msd, "lemma": fields[1].decode(util.UTF8)})
                newnode.text = fields[0].decode(util.UTF8)

                # Append new node.
                if slevel:
                    node.append(newnode)
                else:
                    newsnode.append(newnode)

                if not slevel:
                    # If this ends a sentence, close <s>, attach, and create new <s>.
                    if fields[2].decode(util.UTF8) == sent_end:
                        if len(list(newsnode)) > 0:
                            node.append(newsnode)
                        newsnode = ET.Element(SENTTAG)


def make_fallback_output(node, inputtext):
    """Creates some emergency output in case Freeling crashes for a sentence."""
    newsnode = ET.Element(SENTTAG)
    node.append(newsnode)
    words = inputtext.split()
    for w in words:
        newnode = ET.Element(WORDTAG)
        newnode.text = w.decode(util.UTF8)
        newsnode.append(newnode)


def enqueue_output(out, queue):
    """Auxiliary function needed for reading without blocking."""
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()


if __name__ == "__main__":
    util.run.main(fl_proc)
