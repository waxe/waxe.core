from subprocess import Popen, PIPE
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
        return self._response({'content': '<pre>%s</pre>' % res})
