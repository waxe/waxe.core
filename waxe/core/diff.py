import difflib
from . import utils

class HtmlDiff(difflib.HtmlDiff):

    def _format_line(self, side, flag, linenum, text):
        """Returns HTML markup of "from" / "to" text lines

        side -- 0 or 1 indicating "from" or "to" text
        flag -- indicates if difference on line
        linenum -- line number (used for line number column)
        text -- line text to be marked up
        """
        try:
            linenum = '%d' % linenum
            id = ' id="%s%s"' % (self._prefix[side], linenum)
        except TypeError:
            # handle blank lines where linenum is '>' or ''
            id = ''
        # replace those things that would get confused with HTML symbols
        text = utils.escape_entities(text)

        # make space non-breakable so they don't get compressed or line wrapped
        # text = text.replace(' ','&nbsp;').rstrip()
        css_class = 'diff_to'
        if side == 0:
            css_class = 'diff_from'
        return '<td class="diff_header"%s>%s</td><td class="%s"><pre>%s</pre></td>' \
               % (id, linenum, css_class, text)
