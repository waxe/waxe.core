import os
import logging
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.renderers import render
from ..models import User
from .. import browser
from ..utils import unflatten_params
import xmltool
from xmltool import elements
from urllib2 import HTTPError
from subprocess import Popen, PIPE
import json
from base import JSONHTTPBadRequest, BaseView, BaseUserView

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


class Views(BaseUserView):

    def _get_navigation_data(self, add_previous=False, folder_route='home',
                             file_route='edit', only_json=False):

        def get_data_href(path, key):
            return self.request.route_path(
                '%s_json' % folder_route, _query=[(key, path)])

        def get_href(path, key):
            return self.request.route_path(
                folder_route, _query=[(key, path)])

        def get_file_data_href(path, key):
            return self.request.route_path(
                '%s_json' % file_route, _query=[(key, path)])

        def get_file_href(path, key):
            return self.request.route_path(
                file_route, _query=[(key, path)])

        relpath = self.request.GET.get('path') or ''
        root_path = self.root_path
        abspath = browser.absolute_path(relpath, root_path)
        folders, filenames = browser.get_files(abspath)
        data = {
            'folders': [],
            'filenames': [],
            'previous': None,
            'path': relpath,
        }
        if add_previous and root_path != abspath:
            data['previous'] = {
                'name': '..',
                'data_href': get_data_href(os.path.dirname(relpath), 'path'),
            }
            if not only_json:
                data['previous']['href'] = get_href(os.path.dirname(relpath), 'path')


        for folder in folders:
            dic = {
                'name': folder,
                'data_href': get_data_href(os.path.join(relpath, folder), 'path'),
            }
            if not only_json:
                dic['href'] = get_href(os.path.join(relpath, folder), 'path')
            data['folders'] += [dic]

        for filename in filenames:
            dic = {
                'name': filename,
                'data_href': get_file_data_href(os.path.join(relpath, filename),
                                   'filename'),
            }
            if not only_json:
                dic['href'] = get_file_href(os.path.join(relpath, filename), 'filename')
            data['filenames'] += [dic]
        return data

    def _get_navigation(self):
        data = self._get_navigation_data(add_previous=True)
        return render('blocks/file_navigation.mak',
                      {'data': data}, self.request)

    def _get_breadcrumb_data(self, relpath):
        tple = []
        while relpath:
            name = os.path.basename(relpath)
            tple += [(name, relpath)]
            relpath = os.path.dirname(relpath)

        tple += [('root', '')]
        tple.reverse()
        return tple

    def _get_breadcrumb(self, relpath, force_link=False):
        def get_data_href(path, key):
            return self.request.route_path(
                'home_json', _query=[(key, path)])

        def get_href(path, key):
            return self.request.route_path(
                'home', _query=[(key, path)])

        tple = self._get_breadcrumb_data(relpath)
        html = []
        for index, (name, relpath) in enumerate(tple):
            if index == len(tple) - 1 and not force_link:
                html += ['<li class="active">%s</li>' % (name)]
            else:
                divider = ''
                if len(tple) > 1:
                    divider = '<span class="divider">/</span>'
                html += [(
                    '<li>'
                    '<a data-href="%s" href="%s">%s</a> '
                    '%s'
                    '</li>') % (
                        get_data_href(relpath, 'path'),
                        get_href(relpath, 'path'),
                        name,
                        divider
                    )]
        return ''.join(html)

    @view_config(route_name='home', renderer='index.mak', permission='edit')
    @view_config(route_name='home_json', renderer='json', permission='edit')
    def home(self):
        path = self.request.GET.get('path') or ''
        return self._response({
            'content': self._get_navigation(),
            'breadcrumb': self._get_breadcrumb(path)
        })

    @view_config(route_name='login_selection', renderer='index.mak',
                 permission='edit')
    def login_selection(self):
        logins = self.get_editable_logins()
        login = self.request.GET.get('login')
        if not login or login not in logins:
            raise HTTPBadRequest('Invalid login')

        user = User.query.filter_by(login=login).one()
        self.request.session['editor_login'] = user.login
        self.request.session['root_path'] = user.config.root_path
        return HTTPFound(location='/')

    @view_config(route_name='edit', renderer='index.mak', permission='edit')
    @view_config(route_name='edit_json', renderer='json', permission='edit')
    def edit(self):
        filename = self.request.GET.get('filename') or ''
        if not filename:
            return {
                'error_msg': 'A filename should be provided',
            }
        root_path = self.root_path
        absfilename = browser.absolute_path(filename, root_path)
        try:
            obj = xmltool.load(absfilename)
            html = xmltool.generate_form_from_obj(obj, form_filename=filename)
            jstree_data = obj.to_jstree_dict([])
            if not self._is_json():
                jstree_data = json.dumps(jstree_data)
        except HTTPError, e:
            log.exception(e)
            return {
                'error_msg': 'The dtd of %s can\'t be loaded.' % filename
            }
        except Exception, e:
            log.exception(e)
            return {
                'error_msg': str(e)
            }
        breadcrumb = self._get_breadcrumb(filename)
        return {
            'content': html,
            'breadcrumb': breadcrumb,
            'jstree_data': jstree_data,
        }

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
            html = xmltool.new(dtd_url, dtd_tag)
            return {
                'content': html,
                'breadcrumb': self._get_breadcrumb(None, force_link=True),
            }

        content = render('blocks/new.mak',
                         {'dtd_urls': self.request.dtd_urls,
                          'tags': _get_tags(self.request.dtd_urls[0]),
                         },
                         self.request)
        return {'content': content}

    @view_config(route_name='open_json', renderer='json', permission='edit')
    def open(self):
        data = self._get_navigation_data(folder_route='open', only_json=True)
        relpath = self.request.GET.get('path') or ''
        bdata = self._get_breadcrumb_data(relpath)
        lis = []

        def get_data_href(path, key):
            return self.request.route_path(
                'open_json', _query=[(key, path)])
        for name, path in bdata:
            lis += [{
                'name': name,
                'data_href': get_data_href(path, 'path')
            }]
        data['nav_btns'] = lis
        return data

    @view_config(route_name='create_folder_json', renderer='json', permission='edit')
    def create_folder(self):
        path = self.request.GET.get('path', None)

        if not path:
            return {'status': False, 'error_msg': 'No path given'}

        root_path = self.root_path
        abspath = browser.absolute_path(path, root_path)
        process = Popen(['mkdir', abspath], stdout=PIPE, stderr=PIPE)
        error = process.stderr.read()
        if error:
            return {'status': False, 'error_msg': error}
        return {'status': True}

    @view_config(route_name='update_json', renderer='json', permission='edit')
    def update(self):
        filename = self.request.POST.pop('_xml_filename', None)
        if not filename:
            return {'status': False, 'error_msg': 'No filename given'}

        root_path = self.root_path
        absfilename = browser.absolute_path(filename, root_path)
        try:
            xmltool.update(absfilename, self.request.POST)
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

    @view_config(route_name='update_texts_json', renderer='json', permission='edit')
    def update_texts(self):
        params = unflatten_params(self.request.POST)

        if 'data' not in params or not params['data']:
            return {'status': False, 'error_msg': 'Missing parameters!'}

        root_path = self.root_path
        status = True
        error_msgs = []
        for dic in params['data']:
            filecontent = dic['filecontent']
            filename = dic['filename']
            absfilename = browser.absolute_path(filename, root_path)
            try:
                obj = xmltool.load_string(filecontent)
                obj.write(absfilename)
            except Exception, e:
                status = False
                error_msgs += ['%s: %s' % (filename, str(e))]

        if not status:
            return {'status': False, 'error_msg': '<br />'.join(error_msgs)}

        content = 'Files updated'
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
        dic = elements.get_jstree_json_from_str_id(elt_id, dtd_url=dtd_url)
        dic['status'] = True
        return dic

    @view_config(route_name='get_comment_modal_json', renderer='json',
                 permission='edit')
    def get_comment_modal_json(self):
        comment = self.request.GET.get('comment') or ''
        content = render('blocks/comment_modal.mak',
                         {'comment': comment}, self.request)
        return {'content': content}


class BadRequestView(BaseView):

    @view_config(context=JSONHTTPBadRequest, renderer='json', route_name=None)
    @view_config(context=HTTPBadRequest, renderer='index.mak', route_name=None)
    def bad_request(self):
        """This view is called when there is no selected account and the logged
        user has nothing to edit.
        """
        logins = self.get_editable_logins()
        if not logins:
            if self.user_is_admin():
                link = self.request.route_path('admin_home')
                return {'content': 'Go to your <a href="%s">admin interface</a> '
                                   'to insert a new user' % link}
            return {'content': 'There is a problem with your configuration, '
                    'please contact your administrator with '
                    'the following message: Edit the user named \'%s\' '
                    'and set the root_path in the config.' % self.logged_user.login}

        content = render('blocks/login_selection.mak', {'logins': logins},
                         self.request)
        return {'content': content}


def includeme(config):
    config.add_route('home', '/')
    config.add_route('home_json', '/home.json')
    config.add_route('login_selection', '/login-selection')
    config.add_route('edit', '/edit')
    config.add_route('edit_json', '/edit.json')
    config.add_route('get_tags_json', '/get-tags.json')
    config.add_route('new_json', '/new.json')
    config.add_route('open_json', '/open.json')
    config.add_route('create_folder_json', '/create-folder.json')
    config.add_route('update_json', '/update.json')
    config.add_route('update_text_json', '/update-text.json')
    config.add_route('update_texts_json', '/update-texts.json')
    config.add_route('add_element_json', '/add-element.json')
    config.add_route('get_comment_modal_json', '/get-comment-modal.json')
    config.scan(__name__)
