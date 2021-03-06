import pytest

from resourceful import NeededResources, Library, Resource, Slot, SlotError


def test_fill_slot():
    needed = NeededResources()

    lib = Library('lib', '')

    slot = Slot(lib, '.js')
    a = Resource(lib, 'a.js', depends=[slot])

    b = Resource(lib, 'b.js')

    needed.need(a, {slot: b})

    resources = needed.resources()
    assert len(resources) == 2

    # verify filled slot is correctly
    assert resources[0].library is b.library
    assert resources[0].relpath is b.relpath


def test_dont_fill_required_slot():
    needed = NeededResources()

    lib = Library('lib', '')

    slot = Slot(lib, '.js')
    a = Resource(lib, 'a.js', depends=[slot])

    b = Resource(lib, 'b.js')

    needed.need(a)

    with pytest.raises(SlotError):
        needed.resources()


def test_no_need_to_fill_in_not_required():
    needed = NeededResources()

    lib = Library('lib', '')

    slot = Slot(lib, '.js', required=False)
    a = Resource(lib, 'a.js', depends=[slot])

    needed.need(a)

    # slot wasn't required and not filled in, so filled slot doesn't show up
    assert needed.resources() == [a]


def test_slot_with_default_uses_default_if_nothing_given_in_need():
    needed = NeededResources()
    lib = Library('lib', '')
    default_resource_for_slot = Resource(lib, 'b.js')
    slot = Slot(lib, '.js', default=default_resource_for_slot)
    a = Resource(lib, 'a.js', depends=[slot])
    needed.need(a)
    relpaths = [r.relpath for r in needed.resources()]
    assert relpaths == ['b.js', 'a.js']


def test_default_can_be_overridden():
    needed = NeededResources()
    lib = Library('lib', '')
    default_resource_for_slot = Resource(lib, 'b.js')
    slot = Slot(lib, '.js', default=default_resource_for_slot)
    a = Resource(lib, 'a.js', depends=[slot])
    custom_resource_for_slot = Resource(lib, 'c.js')
    needed.need(a, {slot: custom_resource_for_slot})
    relpaths = [r.relpath for r in needed.resources()]
    assert relpaths == ['c.js', 'a.js']


def test_slot_with_default_can_not_set_required_explicitly():
    lib = Library('lib', '')

    a = Resource(lib, 'a.js')
    with pytest.raises(ValueError):
        slot = Slot(lib, '.js', default=a, required=True)


def test_fill_slot_wrong_extension():
    needed = NeededResources()

    lib = Library('lib', '')

    slot = Slot(lib, '.js')
    a = Resource(lib, 'a.js', depends=[slot])

    b = Resource(lib, 'b.css')

    needed.need(a, {slot: b})

    with pytest.raises(SlotError):
        needed.resources()


def test_fill_slot_wrong_dependencies():
    needed = NeededResources()

    lib = Library('lib', '')

    slot = Slot(lib, '.js')
    a = Resource(lib, 'a.js', depends=[slot])

    c = Resource(lib, 'c.js')

    b = Resource(lib, 'b.js', depends=[c])

    needed.need(a, {slot: b})

    with pytest.raises(SlotError):
        needed.resources()


def test_render_filled_slots():
    needed = NeededResources()

    lib = Library('lib', '')

    slot = Slot(lib, '.js')
    a = Resource(lib, 'a.js', depends=[slot])

    b = Resource(lib, 'b.js')

    needed.need(a, {slot: b})

    assert needed.render() == '''\
<script type="text/javascript" src="/resourceful/lib/b.js"></script>
<script type="text/javascript" src="/resourceful/lib/a.js"></script>'''


def test_slot_depends():

    needed = NeededResources()

    lib = Library('lib', '')

    c = Resource(lib, 'c.js')
    slot = Slot(lib, '.js', depends=[c])
    a = Resource(lib, 'a.js', depends=[slot])
    b = Resource(lib, 'b.js', depends=[c])

    needed.need(a, {slot: b})

    assert needed.render() == '''\
<script type="text/javascript" src="/resourceful/lib/c.js"></script>
<script type="text/javascript" src="/resourceful/lib/b.js"></script>
<script type="text/javascript" src="/resourceful/lib/a.js"></script>'''


def test_slot_depends_subset():
    needed = NeededResources()

    lib = Library('lib', '')

    c = Resource(lib, 'c.js')
    slot = Slot(lib, '.js', depends=[c])
    a = Resource(lib, 'a.js', depends=[slot])
    b = Resource(lib, 'b.js', depends=[])

    needed.need(a, {slot: b})

    assert needed.render() == '''\
<script type="text/javascript" src="/resourceful/lib/c.js"></script>
<script type="text/javascript" src="/resourceful/lib/b.js"></script>
<script type="text/javascript" src="/resourceful/lib/a.js"></script>'''


def test_slot_depends_incorrect():
    needed = NeededResources()

    lib = Library('lib', '')

    c = Resource(lib, 'c.js')
    slot = Slot(lib, '.js', depends=[c])
    a = Resource(lib, 'a.js', depends=[slot])
    d = Resource(lib, 'd.js')
    b = Resource(lib, 'b.js', depends=[d])

    needed.need(a, {slot: b})

    with pytest.raises(SlotError):
        needed.render()


def test_slot_minified():
    needed = NeededResources(minified=True)

    lib = Library('lib', '')

    slot = Slot(lib, '.js')
    a = Resource(lib, 'a.js', depends=[slot])

    b = Resource(lib, 'b.js', minified='b-min.js')

    needed.need(a, {slot: b})
    assert needed.render() == '''\
<script type="text/javascript" src="/resourceful/lib/b-min.js"></script>
<script type="text/javascript" src="/resourceful/lib/a.js"></script>'''


def test_resource_need_should_pass_slots_to_needed():
    import resourceful
    lib = Library('lib', '')
    c = Resource(lib, 'c.js')
    slot = Slot(lib, '.js', depends=[c])
    a = Resource(lib, 'a.js', depends=[slot])
    b = Resource(lib, 'b.js', depends=[c])
    needed = resourceful.init_needed()
    try:
        a.need({slot: c})
    finally:
        resourceful.del_needed()
    assert slot in needed._slots


def test_group_need_should_pass_slots_to_needed():
    import resourceful
    lib = Library('lib', '')
    c = Resource(lib, 'c.js')
    slot = Slot(lib, '.js', depends=[c])
    a = Resource(lib, 'a.js', depends=[slot])
    b = Resource(lib, 'b.js', depends=[c])
    g = resourceful.Group([a, b])
    needed = resourceful.init_needed()
    try:
        g.need({slot: c})
    finally:
        resourceful.del_needed()
    assert slot in needed._slots
