from pyramid.httpexceptions import HTTPBadRequest


class JSONHTTPBadRequest(HTTPBadRequest):
    pass


class BaseViews(object):

    def __init__(self, request):
        self.request = request

    def _is_json(self):
        return self.request.matched_route.name.endswith('_json')


class BaseUserViews(BaseViews):

    def __init__(self, request):

        super(BaseUserViews, self).__init__(request)
        if (not request.root_path and
                request.matched_route.name != 'login_selection'):
            if self._is_json():
                raise JSONHTTPBadRequest('root path not defined')
            raise HTTPBadRequest('root path not defined')
