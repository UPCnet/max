import os
import robotsuite
import unittest
import SimpleHTTPServer
import SocketServer
import threading

from webtest import http
from paste.deploy import loadapp
from functools import partial

from mock import patch
from pyramid_robot.layer import Layer, layered

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header, mock_post
from max.tests import test_manager, test_default_security

STATIC_HTTP_PORT = 8000


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


class myPyramidLayer(Layer):

    defaultBases = ()

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.server = http.StopableWSGIServer.create(self.app, port=9090)
        os.environ['APP_PORT'] = '9090'

    def tearDown(self):
        self.server.shutdown()

PYRAMIDROBOTLAYER = myPyramidLayer()


def test_suite():
    suite = unittest.TestSuite()
    current_dir = os.path.abspath(os.path.dirname(__file__))
    robot_dir = os.path.join(current_dir, 'robot')
    robot_tests = [
        os.path.join('robot', doc) for doc in
        os.listdir(robot_dir) if doc.endswith('.robot') and
        doc.startswith('test_')
    ]
    for test in robot_tests:
        suite.addTests([
            layered(robotsuite.RobotTestSuite(test),
            layer=PYRAMIDROBOTLAYER),
        ])
    return suite
