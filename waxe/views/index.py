from pyramid.view import view_config

@view_config(route_name='home', renderer='index.mak')
def my_view(request):
    return {'content':'waxe project'}

