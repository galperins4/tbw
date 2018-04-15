#!/usr/bin/env python

from Naked.toolshed.shell import muterun_js
from jinja2 import Environment, FileSystemLoader
import sys
import json
import os

class Builder():
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

    def build(self, script, data):
        
        template = self.env.get_template(script + ".py").render({
            **data
        })

        transactionScript=script + ".js"

        with open(transactionScript, "wt") as fh:
            fh.write(template)

        response = muterun_js(transactionScript)

        if response.exitcode == 0:
            os.remove(transactionScript)

            return json.loads(response.stdout.decode('utf-8'))
        else:
            sys.stderr.write(response.stderr.decode('utf-8'))