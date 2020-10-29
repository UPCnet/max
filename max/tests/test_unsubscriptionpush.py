# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header

from functools import partial
from hashlib import sha1
from mock import patch
from paste.deploy import loadapp

import json
import os
import unittest


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.reset_database(self.app)
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

        self.create_user(test_manager)
    # BEGIN TESTS

    def test_unsubscribepush_user_to_context(self):
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='public', write='restricted', subscribe='restricted', invite='restricted'))
        self.testapp.post('/people/%s/subscriptions' % username, json.dumps(subscribe_context), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context['url']).hexdigest()
        self.testapp.post('/contexts/%s/unsubscriptionpush/%s' % (url_hash, username), json.dumps(subscribe_context), oauth2Header(test_manager), status=201)

    def test_subscribepush_user_to_context(self):
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='public', write='restricted', subscribe='restricted', invite='restricted'))
        self.testapp.post('/people/%s/subscriptions' % username, json.dumps(subscribe_context), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context['url']).hexdigest()
        self.testapp.delete('/contexts/%s/subscriptionpush/%s' % (url_hash, username), json.dumps(subscribe_context), oauth2Header(test_manager), status=404)

    def test_unsubscribepush_to_context(self):
        """ El usuario se desuscribe de recibir notificaciones push """
        from .mockers import subscribe_context
        from .mockers import user_status_context
        from .mockers import create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        url_hash = sha1(create_context['url']).hexdigest()
        self.admin_unsubscribepush_user_from_context(username, url_hash, expect=201)
        res = self.create_activity(username, user_status_context)
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['url'], subscribe_context['object']['url'])

    def test_unsubscribepush_to_context_already_subscribed(self):
        """ El usuario se desuscribe de recibir notificaciones push de un contexto que ya esta desuscrito"""
        from .mockers import subscribe_context
        from .mockers import user_status_context
        from .mockers import create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        url_hash = sha1(create_context['url']).hexdigest()        
        self.admin_unsubscribepush_user_from_context(username, url_hash)
        self.admin_unsubscribepush_user_from_context(username, url_hash, expect=200)
        res = self.create_activity(username, user_status_context)
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['url'], subscribe_context['object']['url'])

    def test_unsubscribepush_to_inexistent_context(self):
        """ El usuario se desuscribe de recibir notificaciones push de un contexto que no existe """
        from .mockers import subscribe_context
        from .mockers import create_context
        username = 'messi'
        self.create_user(username)
        url_hash = sha1(create_context['url']).hexdigest()        
        res = self.admin_unsubscribepush_user_from_context(username, url_hash, expect=404)     
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'ObjectNotFound')

    def test_get_all_unsubscribedpush_contexts_for_user(self):
        """ Todos los contextos de los que un usuario se ha desuscrito para no recibir notificaciones push """
        from .mockers import create_context
        from .mockers import subscribe_contextA, create_contextA
        from .mockers import subscribe_contextB, create_contextB
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context, permissions=dict(read='public', write='restricted', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextA, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextB, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_contextA)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_contextA)
        self.admin_subscribe_user_to_context(username, subscribe_contextB)
        url_hashA = sha1(create_contextA['url']).hexdigest()        
        self.admin_unsubscribepush_user_from_context(username, url_hashA)

        res = self.testapp.get('/people/%s/unsubscriptionpush' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('url'), 'http://atenea.upc.edu/A')

    def test_get_all_users_unsubscribedpush_context(self):
        """ Todos los usuarios que se han desuscrito de un contexto para no recibir notificaciones push """
        from .mockers import create_context
        from .mockers import subscribe_contextA, create_contextA
        from .mockers import subscribe_contextB, create_contextB
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context, permissions=dict(read='public', write='restricted', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextA, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextB, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_contextA)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_contextA)
        self.admin_subscribe_user_to_context(username, subscribe_contextB)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_contextB)
        url_hashA = sha1(create_contextA['url']).hexdigest()        
        self.admin_unsubscribepush_user_from_context(username, url_hashA)
        self.admin_unsubscribepush_user_from_context(username_not_me, url_hashA)

        res = self.testapp.get('/contexts/%s/unsubscriptionpush' % url_hashA, "", oauth2Header(test_manager))
        result = json.loads(res.text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].get('username'), 'xavi')
        self.assertEqual(result[1].get('username'), 'messi')


    def test_get_unsubscriptionspush_from_another_user(self):
        """
            Dado un usuario
            Cuando intenta obtener la lista de las desuscripciones push de otro
            Entonces le devuelve un error
        """
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        username2 = 'xavi'
        self.create_user(username2)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        url_hash = sha1(create_context['url']).hexdigest()
        self.admin_unsubscribepush_user_from_context(username, url_hash, expect=201)
        self.testapp.get('/people/%s/unsubscriptionpush' % username, {}, oauth2Header(username2), status=403)

    
    def test_subscribepush_to_context_user(self):
        """
            Dado un usuario
            Cuando esta desuscrito para recibir notificaciones push de un contexto
            Y intenta suscribirse para volver a recibir notificaciones push
            Puede hacerlo
        """
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', subscribe='public', invite='restricted'))
        self.user_subscribe_user_to_context(username, subscribe_context, expect=201)
        url_hash = sha1(create_context['url']).hexdigest()
        self.admin_unsubscribepush_user_from_context(username, url_hash, expect=201)
        self.user_subscribepush_user_from_context(username, url_hash, expect=204)


    def test_subscribepush_to_context_user_already_subscribed(self):
        """
            Dado un usuario
            Cuando esta desuscrito para recibir notificaciones push de un contexto
            Y intenta suscribirse dos veces seguidas para no recibir notificaciones push
            La segunda le da error
        """
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', subscribe='public', invite='restricted'))
        self.user_subscribe_user_to_context(username, subscribe_context, expect=201)
        url_hash = sha1(create_context['url']).hexdigest()
        self.admin_unsubscribepush_user_from_context(username, url_hash, expect=201)
        self.user_subscribepush_user_from_context(username, url_hash, expect=204)
        self.user_subscribepush_user_from_context(username, url_hash, expect=404)