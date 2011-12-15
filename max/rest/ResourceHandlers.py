from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadRequest, HTTPOk, HTTPNotFound, HTTPInternalServerError

import json
from bson import json_util

class ResourceRoot(object):
    """
    """
    response_content_type = 'application/text'

    def __init__(self,context,request):
        """
        """
        self.context=context
        self.request=request

    def buildResponse(self,data):
        """
        """
        response = Response(data)
        response.content_type = self.response_content_type
        return response        


class JSONResourceRoot(ResourceRoot):
    """
    """
    response_content_type = 'application/json'

    def buildResponse(self,data):
        """
            Translate to JSON object if any data. If data is not a list
            something went wrong
        """
        if data:
            if isinstance(data,list):
                response_payload = json.dumps(data, default=json_util.default)
            else:
                return HTTPInternalServerError('Invalid JSON output')
        else:
            response_payload = None

        return super(JSONResourceRoot,self).buildResponse(response_payload)


class ResourceEntity(object):
    """
    """
    response_content_type = 'application/text'

    def __init__(self,context,request):
        """
        """
        self.context=context
        self.request=request

    def buildResponse(self,data):
        """
        """
        if data:
            response = Response(data)
            response.content_type = self.response_content_type
        else:
            response = HTTPNotFound()

        return response        

class JSONResourceEntity(ResourceEntity):
    """
    """
    response_content_type = 'application/json'

    def buildResponse(self,data):
        """
            Translate to JSON object if any data. If data is not a dict,
            something went wrong
        """
        if data:
            if isinstance(data,dict):
                response_payload = json.dumps(data, default=json_util.default)
            else:
                return HTTPInternalServerError('Invalid JSON output')
        else:
            response_payload = None

        return super(JSONResourceEntity,self).buildResponse(response_payload)