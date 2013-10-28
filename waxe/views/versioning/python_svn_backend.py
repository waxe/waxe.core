import os.path
import logging
import pysvn
import locale
from subprocess import Popen, PIPE
from pyramid.renderers import render
from waxe import browser
from waxe import diff
from waxe import models
from waxe.utils import unflatten_params
from ..base import BaseView
from .pysvn_backend import PysvnView



class PythonSvnView(PysvnView):
    """Same class than PysvnView but we call the svn command line to make the
    update since it's very slow to do it with pysvn.
    """

    def update(self):
        p = Popen(self.svn_cmd("update  %s" % self.root_path),
                  shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                  close_fds=True)
        (child_stdout, child_stdin) = (p.stdout, p.stdin)
        error = p.stderr.read()
        if error:
            return {'error_msg': error}

        res = p.stdout.read()
        # We want to display relative urls
        res = res.replace(self.root_path + '/', '')
        return {'content': '<pre>%s</pre>' % res}

