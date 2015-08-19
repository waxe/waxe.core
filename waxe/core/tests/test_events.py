import unittest
from waxe.core import events


class TestEvents(unittest.TestCase):

    def setUp(self):
        self.events = events.events.copy()

    def tearDown(self):
        events.events = self.events

    def test_on(self):
        self.assertFalse('event' in events.events)
        initial_nb = len(events.events)
        events.on('event', lambda: 'Hello')
        self.assertEqual(len(events.events), initial_nb + 1)
        self.assertTrue('event' in events.events)

    def test_trigger(self):
        lis = []

        def increment():
            lis.append(1)

        events.on('event', increment)
        events.trigger('event')
        self.assertEqual(len(lis), 1)

        events.on('event.txt', increment)

        # event.txt and event are triggered
        events.trigger('event.txt')
        self.assertEqual(len(lis), 3)

    def test_trigger_params(self):
        args = [1, 2, 3]
        kw = {'ka': 'a', 'kb': 'b'}

        def func1(a, b, c, ka, kb):
            return a+1, b+1, c+1, ka, kb+'c'

        def func2(a, b, c, ka, kb):
            return a+1, b+1, c+1, ka, kb+'c'

        events.on('params', func1)
        events.on('params', func2)

        res = events.trigger('params', *args, **kw)
        self.assertEqual(res, (3, 4, 5, 'a', 'bcc'))

        def func3(content):
            content += ' updated'
            return content

        events.on('params1', func3)
        res = events.trigger('params1', content='content')
        self.assertEqual(res, 'content updated')

    def test_on_updated(self):
        pass
