import os
import tempfile
import xmltool
from xmltool import dtd_parser, render as xt_render
from lxml import etree
import json

from urllib2 import HTTPError, URLError
from pyramid.view import view_config
from pyramid.renderers import render, Response
from .. import browser, utils
from base import BaseUserView
import pyramid_logging

log = pyramid_logging.getLogger(__name__)

NAV_EDIT = 'edit'
NAV_EDIT_TEXT = 'edit_text'
NAV_DIFF = 'diff'


def _get_tags(dtd_url):
    dic = xmltool.dtd_parser.parse(dtd_url=dtd_url)
    lis = []
    for k, v in dic.items():
        if issubclass(v, xmltool.elements.TextElement):
            continue
        lis += [k]
    lis.sort()
    return lis


class EditorView(BaseUserView):

    def _get_nav_editor(self, filename, kind):
        """Navs to display XML or Source when we edit a file
        """
        html = []
        lis = [
            ('XML', 'edit', NAV_EDIT),
            ('Source', 'edit_text', NAV_EDIT_TEXT),
        ]
        if self.has_versioning():
            lis += [('Diff', 'diff', NAV_DIFF)]

        for name, route, k in lis:
            li_class = ''
            attrs = ''
            if kind == k:
                li_class = ' class="active"'
            else:
                attrs = ' href="%s" data-href="%s"' % (
                    self.request.custom_route_path(route,
                                                   _query=[('path', filename)]),
                    self.request.custom_route_path('%s_json' % route,
                                                   _query=[('path', filename)]),
                )
            html += ['<li%s><a%s>%s</a></li>' % (li_class, attrs, name)]
        return '<ul class="nav nav-tabs">%s</ul>' % ''.join(html)

    @view_config(route_name='edit', renderer='index.mak', permission='edit')
    @view_config(route_name='edit_json', renderer='json', permission='edit')
    def edit(self):
        filename = self.request.GET.get('path')
        if not filename:
            return self._response({
                'error_msg': 'A filename should be provided',
            })
        root_path = self.root_path
        absfilename = browser.absolute_path(filename, root_path)
        iframe = 'iframe' in self.request.GET
        try:
            obj = xmltool.load(absfilename)
            if iframe:
                obj.root.html_render = xt_render.ReadonlyRender()
                html = obj.to_html()
            else:
                html = xmltool.generate_form_from_obj(
                    obj,
                    form_filename=filename,
                    form_attrs={
                        'data-add-href': self.request.custom_route_path('add_element_json'),
                        'data-comment-href': self.request.custom_route_path('get_comment_modal_json'),
                        'data-href': self.request.custom_route_path('update_json'),
                        'data-copy-href': self.request.custom_route_path('copy_json'),
                        'data-paste-href': self.request.custom_route_path('paste_json'),
                    }
                )
            jstree_data = obj.to_jstree_dict([])
            if not self._is_json():
                jstree_data = json.dumps(jstree_data)
        except (HTTPError, URLError), e:
            log.exception(e, request=self.request)
            return self._response({
                'error_msg': 'The dtd of %s can\'t be loaded.' % filename
            })
        except etree.XMLSyntaxError, e:
            log.exception(e, request=self.request)
            return self.edit_text(e)
        except Exception, e:
            log.exception(e, request=self.request)
            return self._response({
                'error_msg': str(e)
            })

        if 'iframe' in self.request.GET:
            return Response(
                render('iframe.mak',
                       self._response({
                           'content': html,
                           'jstree_data': jstree_data,
                       }),
                       self.request))

        self.add_opened_file(filename)
        breadcrumb = self._get_breadcrumb(filename)
        nav = self._get_nav_editor(filename, kind=NAV_EDIT)
        return self._response({
            'content': html,
            'nav_editor': nav,
            'breadcrumb': breadcrumb,
            'jstree_data': jstree_data,
        })

    @view_config(route_name='edit_text', renderer='index.mak', permission='edit')
    @view_config(route_name='edit_text_json', renderer='json', permission='edit')
    def edit_text(self, exception=None):
        filename = self.request.GET.get('path')
        if not filename:
            return self._response({
                'error_msg': 'A filename should be provided',
            })
        root_path = self.root_path
        absfilename = browser.absolute_path(filename, root_path)
        try:
            content = open(absfilename, 'r').read()
            content = content.decode('utf-8')
        except Exception, e:
            log.exception(e, request=self.request)
            return self._response({
                'error_msg': str(e)
            })

        content = utils.escape_entities(content)

        html = u'<form id="xmltool-form" data-href="%s" method="POST">' % (
            self.request.custom_route_path('update_text_json'),
        )
        html += u'<input type="hidden" id="_xml_filename" name="filename" value="%s" />' % filename
        html += u'<textarea class="codemirror" name="filecontent">%s</textarea>' % content
        html += u'</form>'

        breadcrumb = self._get_breadcrumb(filename)
        nav = self._get_nav_editor(filename, kind=NAV_EDIT_TEXT)
        dic = {
            'content': html,
            'nav_editor': nav,
            'breadcrumb': breadcrumb,
        }
        if exception:
            dic['error_msg'] = str(exception)
        return self._response(dic)

    @view_config(route_name='get_tags_json', renderer='json', permission='edit')
    def get_tags(self):
        dtd_url = self.request.GET.get('dtd-url', None)

        if not dtd_url:
            return {}

        return {'tags': _get_tags(dtd_url)}

    @view_config(route_name='new_json', renderer='json', permission='edit')
    def new(self):
        dtd_url = self.request.POST.get('dtd-url') or None
        dtd_tag = self.request.POST.get('dtd-tag') or None

        if dtd_tag and dtd_url:
            try:
                dic = dtd_parser.parse(dtd_url=dtd_url)
            except (HTTPError, URLError), e:
                log.exception(e, request=self.request)
                return {
                    'error_msg': 'The dtd file %s can\'t be loaded.' % dtd_url
                }
            if dtd_tag not in dic:
                return {
                    'error_msg': 'Invalid dtd element: %s (%s)' % (dtd_tag,
                                                                   dtd_url)
                }
            obj = dic[dtd_tag]()
            obj._xml_dtd_url = dtd_url
            html = xmltool.generate_form_from_obj(
                obj,
                form_attrs={
                    'data-add-href': self.request.custom_route_path('add_element_json'),
                    'data-comment-href': self.request.custom_route_path('get_comment_modal_json'),
                    'data-href': self.request.custom_route_path('update_json'),
                    'data-copy-href': self.request.custom_route_path('copy_json'),
                    'data-paste-href': self.request.custom_route_path('paste_json'),
                }
            )
            jstree_data = obj.to_jstree_dict([])
            if not self._is_json():
                jstree_data = json.dumps(jstree_data)
            return {
                'content': html,
                'breadcrumb': self._get_breadcrumb(None, force_link=True),
                'jstree_data': jstree_data,
            }

        content = render('blocks/new.mak',
                         {'dtd_urls': self.request.dtd_urls,
                          'tags': _get_tags(self.request.dtd_urls[0])},
                         self.request)
        return {'modal': content}

    @view_config(route_name='update_json', renderer='json', permission='edit')
    def update(self):
        filename = self.request.POST.pop('_xml_filename', None)
        if not filename:
            return {'status': False, 'error_msg': 'No filename given'}

        root, ext = os.path.splitext(filename)
        if ext != '.xml':
            error_msg = 'No filename extension.'
            if ext:
                error_msg = "Bad filename extension '%s'." % ext
            error_msg += " It should be '.xml'"
            return {
                'status': False,
                'error_msg': error_msg
            }

        root_path = self.root_path
        absfilename = browser.absolute_path(filename, root_path)
        try:
            xmltool.update(absfilename, self.request.POST)
        except (HTTPError, URLError), e:
            log.exception(e, request=self.request)
            return self._response({
                'error_msg': 'The dtd of %s can\'t be loaded.' % filename
            })
        except Exception, e:
            log.exception(e, request=self.request)
            return {'status': False, 'error_msg': str(e)}

        self.add_indexation_task([absfilename])
        return {
            'status': True,
            'breadcrumb': self._get_breadcrumb(filename),
            'nav_editor': self._get_nav_editor(filename, kind=NAV_EDIT)
        }

    @view_config(route_name='update_text_json', renderer='json', permission='edit')
    def update_text(self):
        filecontent = self.request.POST.get('filecontent')
        filename = self.request.POST.get('filename') or ''
        if not filecontent or not filename:
            return {'status': False, 'error_msg': 'Missing parameters!'}
        root_path = self.root_path
        absfilename = browser.absolute_path(filename, root_path)
        try:
            obj = xmltool.load_string(filecontent)
            obj.write(absfilename)
        except Exception, e:
            return {'status': False, 'error_msg': str(e)}

        content = 'File updated'
        if self.request.POST.get('commit'):
            content = render('blocks/commit_modal.mak',
                             {}, self.request)

        self.add_indexation_task([absfilename])
        return {'status': True, 'content': content}

    @view_config(route_name='add_element_json', renderer='json',
                 permission='edit')
    def add_element_json(self):
        elt_id = self.request.GET.get('elt_id')
        dtd_url = self.request.GET.get('dtd_url')
        if not elt_id or not dtd_url:
            return {'status': False, 'error_msg': 'Bad parameter'}
        dic = xmltool.elements.get_jstree_json_from_str_id(elt_id,
                                                           dtd_url=dtd_url)
        dic['status'] = True
        return dic

    @view_config(route_name='copy_json', renderer='json', permission='edit')
    def copy_json(self):
        if 'elt_id' not in self.request.POST:
            return self._response({'error_msg': 'Bad parameter'})
        data = xmltool.utils.unflatten_params(self.request.POST)
        # Write the content to paste in a temporary file
        filename = tempfile.mktemp()
        open(filename, 'w').write(json.dumps(data))
        self.request.session['clipboard'] = {
            'filename': filename,
            'elt_id': self.request.POST['elt_id'],
        }
        return self._response({'info_msg': 'Copied'})

    @view_config(route_name='paste_json', renderer='json', permission='edit')
    def paste_json(self):
        # TODO: Perhaps we should validate it's the same dtd
        elt_id = self.request.POST.pop('elt_id', None)
        dtd_url = self.request.POST.pop('dtd_url', None)
        data = xmltool.utils.unflatten_params(self.request.POST)

        if not elt_id or not dtd_url:
            return self._response({'error_msg': 'Bad parameter'})

        clipboard = self.request.session.get('clipboard')
        if not clipboard:
            return self._response({
                'error_msg': 'Empty clipboard'
            })
        filename = clipboard['filename']
        source_id = clipboard['elt_id']
        clipboard_data = json.loads(open(filename, 'r').read())

        obj = xmltool.elements.add_new_element_from_id(
            elt_id, source_id, data,
            clipboard_data, dtd_url,
            # Don't keep the attributes nor the comments
            skip_extra=True)
        if not obj:
            return self._response({
                'error_msg': 'The element can\'t be pasted here'
            })

        dic = xmltool.elements.get_display_data_from_obj(obj)
        return self._response(dic)

    @view_config(route_name='get_comment_modal_json', renderer='json',
                 permission='edit')
    def get_comment_modal_json(self):
        comment = self.request.GET.get('comment') or ''
        content = render('blocks/comment_modal.mak',
                         {'comment': comment}, self.request)
        return {'content': content}

    @view_config(route_name='diff', renderer='index.mak', permission='edit')
    @view_config(route_name='diff_json', renderer='json', permission='edit')
    def diff(self):
        filename = self.request.GET.get('path', '')
        if not filename:
            return {'error_msg': 'No filename given'}

        absfilename = browser.absolute_path(filename, self.root_path)
        if not os.path.isfile(absfilename):
            return self._response({
                'error_msg': 'File %s doesn\'t exist' % filename
            })

        vobj = self.get_versioning_obj()
        lis = vobj.diff(filename)
        content = ''
        for l in lis:
            l = utils.escape_entities(l)
            content += '<pre>%s</pre>' % l

        if not content:
            content = '<br />The file is not modified!'

        nav = self._get_nav_editor(filename, kind=NAV_DIFF)
        breadcrumb = self._get_breadcrumb(filename)

        return self._response({
            'breadcrumb': breadcrumb,
            'nav_editor': nav,
            'content': content,
        })


def includeme(config):
    config.add_route('edit', '/edit')
    config.add_route('edit_json', '/edit.json')
    config.add_route('edit_text', '/edit-text')
    config.add_route('edit_text_json', '/edit-text.json')
    config.add_route('get_tags_json', '/get-tags.json')
    config.add_route('new_json', '/new.json')
    config.add_route('update_json', '/update.json')
    config.add_route('update_text_json', '/update-text.json')
    config.add_route('add_element_json', '/add-element.json')
    config.add_route('get_comment_modal_json', '/get-comment-modal.json')
    config.add_route('copy_json', '/copy.json')
    config.add_route('paste_json', '/paste.json')
    config.add_route('diff', '/diff')
    config.add_route('diff_json', '/diff.json')
    config.scan(__name__)
