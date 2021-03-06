import pytest
import webob

from resourceful import (Library, Resource,
                       get_needed, make_serf, compat)
from resourceful import Resourceful, ConfigurationError


def test_inject():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    def app(environ, start_response):
        start_response('200 OK', [])
        needed = get_needed()
        needed.need(y1)
        return [b'<html><head></head><body</body></html>']

    wrapped_app = Resourceful(app, base_url='http://testapp')

    request = webob.Request.blank('/')
    request.environ['SCRIPT_NAME'] = '/root'  # base_url is defined so SCRIPT_NAME
                                              # shouldn't be taken into account
    response = request.get_response(wrapped_app)
    assert response.body == b'''\
<html><head><link rel="stylesheet" type="text/css" href="http://testapp/resourceful/foo/b.css" />
<script type="text/javascript" src="http://testapp/resourceful/foo/a.js"></script>
<script type="text/javascript" src="http://testapp/resourceful/foo/c.js"></script></head><body</body></html>'''


def test_inject_script_name():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    def app(environ, start_response):
        start_response('200 OK', [])
        needed = get_needed()
        needed.need(y1)
        return [b'<html><head></head><body</body></html>']

    wrapped_app = Resourceful(app)

    request = webob.Request.blank('/path')
    request.environ['SCRIPT_NAME'] = '/root'
    response = request.get_response(wrapped_app)
    assert response.body == b'''\
<html><head><link rel="stylesheet" type="text/css" href="/root/resourceful/foo/b.css" />
<script type="text/javascript" src="/root/resourceful/foo/a.js"></script>
<script type="text/javascript" src="/root/resourceful/foo/c.js"></script></head><body</body></html>'''


def test_incorrect_configuration_options():
    app = None
    with pytest.raises(TypeError) as e:
        Resourceful(app, incorrect='configoption')
    assert (
        "__init__() got an unexpected "
        "keyword argument 'incorrect'") in str(e)


def test_inject_unicode_base_url():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')

    def app(environ, start_response):
        start_response('200 OK', [])
        x1.need()
        return [b'<html><head></head><body</body></html>']

    request = webob.Request.blank('/')
    wrapped = Resourceful(app, base_url=compat.u('http://localhost'))
    # Resourceful used to choke on unicode content.
    request.get_response(wrapped)


def test_serf():
    pytest.importorskip('mypackage')
    # also test serf config
    d = {
        'resource': 'py:mypackage.style'
    }
    serf = make_serf({}, **d)
    serf = Resourceful(serf, versioning=False)
    request = webob.Request.blank('/')
    response = request.get_response(serf)
    assert response.body == b'''\
<html><head><link rel="stylesheet" type="text/css" href="/resourceful/foo/style.css" /></head><body></body></html>'''


def test_serf_unknown_library():
    d = {
        'resource': 'unknown_library:unknown_resource'
    }
    with pytest.raises(ConfigurationError):
        make_serf({}, **d)
