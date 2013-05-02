# -*- coding: utf-8 -*-
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPInternalServerError

import json


class ResourceRoot(object):
    """
    """
    response_content_type = 'application/text'

    def __init__(self, data, status_code=200, stats=False, extension={}):
        """
        """
        self.data = data
        self.status_code = status_code
        self.extension = extension
        self.stats = stats
        self.headers = {}

    def wrap(self):
        """
        """
        wrapper = {"items": self.data,
                   "totalItems": len(self.data)}
        wrapper.update(self.extension)
        return wrapper

    def buildResponse(self, payload=None):
        """
        """
        data = payload is None and self.data or payload
        response = Response(data, status_int=self.status_code)
        response.content_type = self.response_content_type
        for key, value in self.headers.items():
            response.headers.add(key, value)
        return response


class JSONResourceRoot(ResourceRoot):
    """
    """
    response_content_type = 'application/json'

    def buildResponse(self, payload=None):
        """
            Translate to JSON object if any data. If data is not a list
            something went wrong
        """
        if self.data:
            if isinstance(self.data, list):
                response_payload = json.dumps(self.wrap())
            elif self.stats and isinstance(self.data, int):
                response_payload = ''
                self.headers['X-totalItems'] = str(self.data)
            else:
                return HTTPInternalServerError('Invalid JSON output')
        else:
            response_payload = json.dumps(self.wrap())

        return super(JSONResourceRoot, self).buildResponse(payload=response_payload)


class ResourceEntity(object):
    """
    """

    response_content_type = 'application/text'

    def __init__(self, data, status_code=200):
        """
        """
        self.data = data
        self.status_code = status_code

    def buildResponse(self, payload=None):
        """
        """
        data = payload is None and self.data or payload
        if data:
            response = Response(data, status_int=self.status_code)
            response.content_type = self.response_content_type
        else:
            response = HTTPNotFound()

        return response


class JSONResourceEntity(ResourceEntity):
    """
    """
    response_content_type = 'application/json'

    def buildResponse(self, payload=None):
        """
            Translate to JSON object if any data. If data is not a dict,
            something went wrong
        """
        if self.data:
            if isinstance(self.data, dict):
                response_payload = json.dumps(self.data)
            else:
                return HTTPInternalServerError('Invalid JSON output')
        else:
            response_payload = None

        return super(JSONResourceEntity, self).buildResponse(payload=response_payload)
