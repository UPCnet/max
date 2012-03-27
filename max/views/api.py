from pyramid.security import authenticated_userid
from pyramid.renderers import get_renderer


class TemplateAPI(object):

    def __init__(self, context, request, page_title=None):
        self.context = context
        self.request = request

    @property
    def masterTemplate(self):
        master = get_renderer('max:templates/master.pt').implementation()
        return master

    @property
    def authenticatedUser(self):
        return authenticated_userid(self.request)

    _snippets = None

    @property
    def snippets(self):
        if self._snippets is None:
            self._snippets = get_renderer('max:templates/snippets.pt').implementation()
        return self._snippets

    _status_message = None

    def getStatusMessage(self):
        if self._status_message:
            return self._status_message
        return self.request.session.pop_flash('info')

    def setStatusMessage(self, value):
        self._status_message = value

    statusMessage = property(getStatusMessage, setStatusMessage)

    _error_message = None

    def getErrorMessage(self):
        if self._error_message:
            return self._error_message
        return self.request.params.get("errorMessage", None)

    def setErrorMessage(self, value):
        self._error_message = value

    errorMessage = property(getErrorMessage, setErrorMessage)

    @property
    def application_url(self):
        app_url = self.request.application_url
        vh = self.getVirtualHost()
        if vh:
            return vh
        else:
            return app_url

    def getVirtualHost(self):
        return self.request.headers.get('X-Virtual-Host-Uri', None)
