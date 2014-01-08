import logging
import os
import xmltool
from xmltool import dtd_parser
from lxml import etree
import json

from urllib2 import HTTPError, URLError
from pyramid.view import view_config
from pyramid.renderers import render
from .. import browser
from ..utils import unflatten_params
from base import BaseUserView

log = logging.getLogger(__name__)


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
        try:
            obj = xmltool.load(absfilename)
            html = xmltool.generate_form_from_obj(
                obj,
                form_filename=filename,
                form_attrs={
                    'data-add-href': self.request.custom_route_path('add_element_json'),
                    'data-comment-href': self.request.custom_route_path('get_comment_modal_json'),
                    'data-href': self.request.custom_route_path('update_json'),
                }
            )
            jstree_data = obj.to_jstree_dict([])
            if not self._is_json():
                jstree_data = json.dumps(jstree_data)
        except (HTTPError, URLError), e:
            log.exception(e)
            return self._response({
                'error_msg': 'The dtd of %s can\'t be loaded.' % filename
            })
        except etree.XMLSyntaxError, e:
            log.exception(e)
            return self.edit_text(e)
        except Exception, e:
            log.exception(e)
            return self._response({
                'error_msg': str(e)
            })
        breadcrumb = self._get_breadcrumb(filename)
        return self._response({
            'content': html,
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
        except Exception, e:
            log.exception(e)
            return self._response({
                'error_msg': str(e)
            })

        html = '<form id="xmltool-form" data-href="%s" method="POST">' % (
            self.request.custom_route_path('update_text_json'),
        )
        html += '<input type="hidden" id="_xml_filename" name="filename" value="%s" />' % filename
        html += '<textarea class="form-control" name="filecontent">%s</textarea>' % content
        html += '</form>'

        breadcrumb = self._get_breadcrumb(filename)
        dic = {
            'content': html,
            'breadcrumb': breadcrumb,
        }
        if exception:
            dic['error_msg'] = str(exception)
        return self._response(dic)

    @view_config(route_name='get_tags_json', renderer='json', permission='edit')
    def get_tags(self):
        dtd_url = self.request.GET.get('dtd_url', None)

        if not dtd_url:
            return {}

        return {'tags': _get_tags(dtd_url)}

    @view_config(route_name='new_json', renderer='json', permission='edit')
    def new(self):
        dtd_url = self.request.GET.get('dtd_url') or None
        dtd_tag = self.request.GET.get('dtd_tag') or None

        if dtd_tag and dtd_url:
            try:
                dic = dtd_parser.parse(dtd_url=dtd_url)
            except (HTTPError, URLError), e:
                log.exception(e)
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
        return {'content': content}

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
            log.exception(e)
            return self._response({
                'error_msg': 'The dtd of %s can\'t be loaded.' % filename
            })
        except Exception, e:
            log.exception(e)
            return {'status': False, 'error_msg': str(e)}

        return {
            'status': True,
            'breadcrumb': self._get_breadcrumb(filename)
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

    @view_config(route_name='get_comment_modal_json', renderer='json',
                 permission='edit')
    def get_comment_modal_json(self):
        comment = self.request.GET.get('comment') or ''
        content = render('blocks/comment_modal.mak',
                         {'comment': comment}, self.request)
        return {'content': content}


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
    config.scan(__name__)
