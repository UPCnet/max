import sys
import os
import re
import shutil
import subprocess
import json

PADDING = 12

files = ['ca/apirest.rst', 'ca/apioperations.rst']

for filename in files:

    # Bakckup file
    shutil.copy(filename, filename + '.backup')

    # Write file with print statements
    apirest = open(filename).read()
    newtext = re.sub(r'>>> response\n', '>>> print response\n', apirest)
    open(filename, 'w').write(newtext)

    # Execute doctests to capture new outputs and restore backup
    output = subprocess.Popen(["/var/pyramid/maxdevel/bin/test", "-t", filename], stdout=subprocess.PIPE).communicate()[0]
    shutil.copy(filename + '.backup', filename)
    os.remove(filename + '.backup')
    # Parse printed blocks with expected results
    prints = re.findall(r'Failed example:\s+print response.*?Got:.*?({.*?)\n[-\n]', output, re.DOTALL)

    # Make json pretty
    pretty = [json.dumps(json.loads(a), indent=4) for a in prints]

    # Add left paddding
    padded = ['\n'.join([(' ' * PADDING) + a for a in json.dumps(json.loads(a), indent=4).split('\n')]) for a in prints]

    # Replace each expected block with the new one
    apirest = open(filename).read()
    newapirest = ''
    last = 0

    expecteds = [match.start() for match in re.finditer(r'\n[\t ]+\.\.\s+->\s+expected', apirest)]
    if len(expecteds) != len(padded):
        print "Expected responses ({}) doesn't match printed responses ({})".format(len(expecteds), len(padded))
        sys.exit(1)
    for pos, expected in enumerate(expecteds):
        current_block = apirest[last:expected]
        last_codeblock = [match.start() + len(match.group()) for match in re.finditer(r'code-block::\s+python\n', current_block)][-1]
        newapirest += current_block[:last_codeblock]

        # Insert new json from previously parsed items
        newapirest += '\n{}\n'.format(padded[pos])
        last = int(expected)

    newapirest += apirest[last:]
    open(filename, 'w').write(newapirest)
