import logging
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.renderers import render
from ..models import User
from base import JSONHTTPBadRequest, BaseView, BaseUserView

log = logging.getLogger(__name__)


class IndexView(BaseUserView):

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
    config.add_route('login_selection', '/login-selection')
    config.scan(__name__)
