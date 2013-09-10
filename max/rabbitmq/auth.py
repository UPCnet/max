# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.response import Response


@view_config(route_name='auth_user', request_method='GET')
def auth_user(context, request):
    #print 'auth_user'
    #print request.params.items()
    return Response('allow administrator')


@view_config(route_name='auth_vhost', request_method='GET')
def auth_vhost(context, request):
    #print 'auth_vhost'
    #print request.params.items()
    return Response('allow')


@view_config(route_name='auth_resource', request_method='GET')
def auth_resource(context, request):
    #print 'auth_resource'
    #print request.params.items()
    return Response('allow')
