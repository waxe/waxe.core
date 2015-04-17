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
        # TODO: this function will be removed soon
        location = self.request.custom_route_path('explore_json')
        if self.request.query_string:
            location += '?%s' % self.request.query_string
        return HTTPFound(location=location)


class IndexView2(JSONBaseUserView):

    @view_config(route_name='profile', permission='authenticated')
    def profile(self):
        return self._profile()


def includeme(config):
    config.add_route('redirect', '/')
    config.add_route('profile', '/profile.json')
    config.scan(__name__)
