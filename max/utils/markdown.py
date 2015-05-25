import mistune
import re


def extract(text, target, status, extracted, default):
    if re.match(r'^  [\{\}]', text):
        text = '  ' + text
    if status == 'extract':
        extracted.setdefault(target, [])
        extracted[target].append(text)
    else:
        default.append(text)


def reformat_markdown(text):

    md = mistune.Markdown()
    tokens = md.block(text)

    reparsed = []

    list_parsing = None
    target = None
    last_token = {'type': ''}

    extracted = {}
    for token in tokens:

        if token['type'] == 'list_start':
            list_parsing = 'initial'
            last_token = token
            continue

        if list_parsing == 'initial' and token['type'] == 'loose_item_start':
            list_parsing = 'title'
            last_token = token
            continue

        if list_parsing == 'title' and token['type'] == 'text':
            if token['text'] == 'Request':
                list_parsing = 'extract'
                target = 'Request'
                last_token = token
                continue
            else:
                extract('+ ' + token['text'], target, list_parsing, extracted, reparsed)
                list_parsing = None
                last_token = token
                continue

        if list_parsing == 'extract' and token['type'] == 'list_item_end':
            list_parsing = None
            last_token = token
            continue

        if last_token['type'] == 'list_item_start' and list_parsing != 'extract':
            extract('- ' + token['text'], target, list_parsing, extracted, reparsed)
        elif token['type'] == 'paragraph':
            extract('\n{}\n'.format(token['text']), target, list_parsing, extracted, reparsed)
        elif token['type'] == 'text':
            extract(token['text'], target, list_parsing, extracted, reparsed)
        elif token['type'] == 'newline':
            extract('', target, list_parsing, extracted, reparsed)
        elif token['type'] == 'code':
            extract(re.sub(r'(^|\n)', r'\1      ', token['text']).rstrip(), target, list_parsing, extracted, reparsed)

        last_token = token

    reformatted = '\n'.join(reparsed)
    extractions = {k: '\n'.join(v).strip('\n') for k, v in extracted.items()}
    return reformatted, extractions
