import unittest
from waxe.core import events


class TestEvents(unittest.TestCase):

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

    def test_on_updated(self):
        pass
