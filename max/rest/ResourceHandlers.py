# -*- coding: utf-8 -*-
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPInternalServerError

import json


class ResourceRoot(object):
    """
    """
    response_content_type = 'application/text'

    def __init__(self, data, status_code=200, stats=False):
        """
        """
        self.data = data
        self.status_code = status_code
        self.stats = stats
        self.headers = {}

    def wrap(self):
        """
        """
        wrapper = self.data
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

        if self.stats:
            response_payload = ''
            self.headers['X-totalItems'] = str(self.data)
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
        response = Response(data, status_int=self.status_code)
        response.content_type = self.response_content_type

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
        response_payload = json.dumps(self.data)

        return super(JSONResourceEntity, self).buildResponse(payload=response_payload)
