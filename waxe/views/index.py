from pyramid.view import view_config, view_defaults


@view_defaults(renderer='index.mak')
class Views(object):

    def __init__(self, request):
        self.request = request

    @view_config(route_name='home', renderer='index.mak', permission='edit')
    def home(self):
        return {'content': 'home content'}


def includeme(config):
    config.add_route('home', '/')
