import webob

from resourceful.config import convert_config
from resourceful import (Injector, Delegator, Publisher, LibraryRegistry,
                       ConfigurationError)
import resourceful


def Resourceful(app,
              publisher_signature=resourceful.DEFAULT_SIGNATURE,
              **config):
    """Resourceful WSGI framework component.

    :param app: The WSGI app to wrap with Resourceful.

    :param publisher_signature: Optional argument to define the
      signature of the publisher in a URL. The default is ``resourceful``.

    :param ``**config``: Optional keyword arguments. These are
      passed to :py:class:`NeededInclusions` when it is constructed.
    """
    # Wrap the app inside the injector middleware, inside the
    # delegator middleware.
    injector = Injector(
        app,
        publisher_signature=publisher_signature,
        **config)

    publisher = Publisher(LibraryRegistry.instance())

    return Delegator(
        injector,
        publisher,
        publisher_signature=publisher_signature)


def make_resourceful(app, global_config, **local_config):
    local_config = convert_config(local_config)
    return Resourceful(app, **local_config)


class Serf(object):
    """Serf WSGI application.

    Serve a very simple HTML page while needing a resource. Can be
    configured behind the :py:func:`Resourceful` WSGI framework
    component to let the resource be included.

    :param resource: The :py:class:`Resource` to include.
    """

    def __init__(self, resource):
        self.resource = resource

    @webob.dec.wsgify
    def __call__(self, request):
        """This WSGI app returns a single page with the listed resources.
        """
        self.resource.need()
        return webob.Response('<html><head></head><body></body></html>')


def make_serf(global_config, **local_config):
    resource_identifier = local_config['resource']
    # only accept 'py:' library identifiers at this point
    if resource_identifier.startswith('py:'):
        dotted_name = resource_identifier[3:]
        resource = resolve(dotted_name)
    else:
        raise ConfigurationError("Unknown library identifier")
    return Serf(resource)


# taken from zope.dottedname.resolve
def resolve(name, module=None):
    name = name.split('.')
    if not name[0]:
        if module is None:
            raise ValueError("relative name without base module")
        module = module.split('.')
        name.pop(0)
        while not name[0]:
            module.pop()
            name.pop(0)
        name = module + name

    used = name.pop(0)
    found = __import__(used)
    for n in name:
        used += '.' + n
        try:
            found = getattr(found, n)
        except AttributeError:
            __import__(used)
            found = getattr(found, n)

    return found
