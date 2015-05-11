import pyramid.httpexceptions as exc
from waxe.core import browser

events = {}


def on(eventname, callback):
    """Register an callback associated to an event name
    """
    global events
    events.setdefault(eventname, []).append(callback)


def trigger(eventname, *args, **kw):
    """Trigger an event. It calls all the callback associated to this event
    name.

    2 levels definition
    >>> events.on('ev.all', lambda: True)
    >>> events.on('ev', lambda: False)

    When you call events.trigger('ev') the callbacks of 'ev.all' and 'ev' will
    be called
    """
    global events
    eventnames = [eventname]
    base_eventname = eventname.split('.')[0]
    if base_eventname != eventname:
        eventnames += [base_eventname]

    for eventname in eventnames:
        callbacks = events.get(eventname)
        if not callbacks:
            continue
        for callback in callbacks:
            callback(*args, **kw)


def on_updated(view, path=None, paths=None):
    # TODO: Use logging instead of errors?
    if path is None and paths is None:
        raise exc.HTTPClientError(
            'No filename given when triggering saved')
    if path and paths:
        raise exc.HTTPClientError(
            'Both path and paths should not be defined when triggering saved')

    if path:
        paths = [path]

    lis = []
    for path in paths:
        lis += [browser.absolute_path(path, view.root_path)]
    view.add_indexation_task(lis)


on('updated', on_updated)
on('deleted', on_updated)
