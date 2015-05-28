# -*- coding: utf-8 -*-
import re
import json

def_links = r' *\[([^^\]]+)\]: *<?([^\s>]+)>?(?: +["(]([^\n]+)[")])? *(?:\n+|$)'
def_footnotes = r'\[\^([^\]]+)\]: *([^\n]*(?:\n+|$)(?: {1,}[^\n]*(?:\n+|$))*)'
def_list_block = r'\n( *)([*+-]|\d+\.) %%s([\s\S])+?(?:\n+(?=\1?(?:[-*_] *){3,}(?:\n+|$))|\n+(?=%s)|\n+(?=%s)|\n{2,}(?! )(?!\1(?:[*+-]|\d+\.) )\n*|\s*$)' % (def_links, def_footnotes)

list_block = re.compile(def_list_block % (''))
request_block = re.compile(def_list_block % ('Request'))


def extract_first_request(text, remove=True):
    """
        Extracts a Request section from the text
    """
    match = request_block.search(text)
    extraction = None
    if match:
        jsonmatch = re.search(r'.*?(\{.*\})', match.group(), re.DOTALL)
        if jsonmatch:
            text = text[:match.start()] + text[match.end():]
            try:
                jsonobject = json.loads(jsonmatch.groups()[0])
            except:
                extraction = jsonmatch.groups()[0]
            else:
                extraction = json.dumps(jsonobject, indent=4)

    return text, extraction


def reformat_markdown(text):
    """
        Extract known sections from text and returns reformatted original
        text without the extracted sections, and the extracted sections.
    """
    extracted = {}

    def apply_extract(name, method, text):
        text, extraction = method(text)
        if extraction:
            extracted[name] = extraction
        return text

    text = apply_extract('request', extract_first_request, text)

    return text, extracted
