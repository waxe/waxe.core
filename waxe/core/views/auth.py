from pyramid.security import (
    unauthenticated_userid,
    remember,
    forget,
)
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPForbidden
from pyramid_auth import forms
import tw2.core as twc
from .base import JSONView
import pyramid.httpexceptions as exc


@view_config(context=exc.HTTPException, renderer='json')
def exception_view(context, request):
    """Returns HTTP error responses as json
    """
    request.response.status = context._status
    return str(context)


@view_config(context=HTTPForbidden, renderer='json')
def forbidden_view(request):
    # NOTE: we can't raise httpexception in this function since we are already
    # raising one when we call it
    if unauthenticated_userid(request):
        # The user is logged but doesn't have the right permission
        request.response.status_int = 403
        return 'Missing permission'

    request.response.status_int = 401
    return 'You are not logged'


class LoginView(JSONView):

    @view_config(route_name='login', request_method='POST')
    def login(self):
        validate_func = self.request.registry.settings[
            'pyramid_auth.validate_function']
        LoginForm = forms.create_login_form(self.request,
                                            validate_func)
        widget = LoginForm().req()
        params = self.req_post

        if not params:
            raise exc.HTTPClientError()

        try:
            data = widget.validate(params)
        except twc.ValidationError:
            raise exc.HTTPUnauthorized()

        headers = remember(self.request, data['login'])
        self.request.response.headerlist.extend(headers)
        return True

    @view_config(route_name='logout', request_method='GET')
    def logout(self):
        headers = forget(self.request)
        self.request.response.headerlist.extend(headers)
        return 'You are logged off'


def includeme(config):
    config.add_route(
        'login',
        '/login.json',
    )

    config.add_route(
        'logout',
        '/logout.json',
    )

    config.scan(__name__)
