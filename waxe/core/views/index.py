import urlparse
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
import pyramid.httpexceptions as exc
from pyramid.renderers import render
from ..models import User
from base import (
    JSONHTTPBadRequest,
    BaseView,
    BaseUserView,
    JSONView,
    JSONBaseUserView
)


class IndexView(BaseUserView):

    @view_config(route_name='redirect', permission='edit')
    def redirect(self):
        location = self.request.custom_route_path('home')
        if self.request.query_string:
            location += '?%s' % self.request.query_string
        return HTTPFound(location=location)


class IndexView2(JSONBaseUserView):

    @view_config(route_name='profile', permission='authenticated')
    def profile(self):
        return self._profile()


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
                return self._response(
                    {'content': 'Go to your <a href="%s">admin interface</a> '
                                'to insert a new user' % link})
            return self._response(
                {'content': 'There is a problem with your configuration, '
                            'please contact your administrator with '
                            'the following message: '
                            'Edit the user named \'%s\' '
                            'and set the root_path in the config.' %
                            self.logged_user.login})

        qs = self.request.query_string
        qs = urlparse.parse_qsl(qs)
        content = render('blocks/login_selection.mak',
                         {'logins': logins,
                          'qs': qs,
                          'last_files': self._get_last_files()
                         },
                         self.request)
        return self._response({'content': content})


def includeme(config):
    config.add_route('redirect', '/')
    config.add_route('profile', '/profile.json')
    config.scan(__name__)
