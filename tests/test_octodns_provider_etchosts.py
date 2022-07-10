#
#
#

from os import path
from os.path import isfile
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

from octodns.provider.plan import Plan
from octodns.record import Record
from octodns.zone import Zone

from octodns_etchosts import EtcHostsProvider


class TemporaryDirectory(object):
    def __init__(self, delete_on_exit=True):
        self.delete_on_exit = delete_on_exit

    def __enter__(self):
        self.dirname = mkdtemp()
        return self

    def __exit__(self, *args, **kwargs):
        if self.delete_on_exit:
            rmtree(self.dirname)
        else:
            raise Exception(self.dirname)


class TestEtcHostsProvider(TestCase):
    def test_provider(self):
        source = EtcHostsProvider('test', 'not-used')

        zone = Zone('unit.tests.', [])

        # We never populate anything, when acting as a source
        source.populate(zone, target=source)
        self.assertEqual(0, len(zone.records))
        # Same if we're acting as a target
        source.populate(zone)
        self.assertEqual(0, len(zone.records))

        record = Record.new(
            zone, '', {'ttl': 60, 'type': 'ALIAS', 'value': 'www.unit.tests.'}
        )
        zone.add_record(record)

        record = Record.new(
            zone,
            'www',
            {'ttl': 60, 'type': 'AAAA', 'value': '2001:4860:4860::8888'},
        )
        zone.add_record(record)
        record = Record.new(
            zone,
            'www',
            {'ttl': 60, 'type': 'A', 'values': ['1.1.1.1', '2.2.2.2']},
        )
        zone.add_record(record)

        record = record.new(
            zone,
            'v6',
            {'ttl': 60, 'type': 'AAAA', 'value': '2001:4860:4860::8844'},
        )
        zone.add_record(record)

        record = record.new(
            zone,
            'start',
            {'ttl': 60, 'type': 'CNAME', 'value': 'middle.unit.tests.'},
        )
        zone.add_record(record)
        record = record.new(
            zone, 'middle', {'ttl': 60, 'type': 'CNAME', 'value': 'unit.tests.'}
        )
        zone.add_record(record)

        record = record.new(
            zone, 'ext', {'ttl': 60, 'type': 'CNAME', 'value': 'github.com.'}
        )
        zone.add_record(record)

        record = record.new(
            zone, '*', {'ttl': 60, 'type': 'A', 'value': '3.3.3.3'}
        )
        zone.add_record(record)

        with TemporaryDirectory() as td:
            # Add some subdirs to make sure that it can create them
            directory = path.join(td.dirname, 'sub', 'dir')
            hosts_file = path.join(directory, 'unit.tests.hosts')
            target = EtcHostsProvider('test', directory)

            # We add everything
            plan = target.plan(zone)
            self.assertEqual(len(zone.records), len(plan.changes))
            self.assertFalse(isfile(hosts_file))

            # Now actually do it
            self.assertEqual(len(zone.records), target.apply(plan))
            self.assertTrue(isfile(hosts_file))

            with open(hosts_file) as fh:
                data = fh.read()
                # v6
                self.assertTrue('2001:4860:4860::8844\tv6.unit.tests' in data)
                # www
                self.assertTrue('1.1.1.1\twww.unit.tests' in data)
                # root ALIAS
                self.assertTrue('# unit.tests -> www.unit.tests' in data)
                self.assertTrue('1.1.1.1\tunit.tests' in data)

                self.assertTrue(
                    '# start.unit.tests -> middle.unit.tests' in data
                )
                self.assertTrue('# middle.unit.tests -> unit.tests' in data)
                self.assertTrue('# unit.tests -> www.unit.tests' in data)
                self.assertTrue('1.1.1.1	start.unit.tests' in data)

            # second empty run that won't create dirs and overwrites file
            plan = Plan(zone, zone, [], True)
            self.assertEqual(0, target.apply(plan))

    def test_cname_loop(self):
        source = EtcHostsProvider('test', 'not-used')

        zone = Zone('unit.tests.', [])

        # We never populate anything, when acting as a source
        source.populate(zone, target=source)
        self.assertEqual(0, len(zone.records))
        # Same if we're acting as a target
        source.populate(zone)
        self.assertEqual(0, len(zone.records))

        record = Record.new(
            zone,
            'start',
            {'ttl': 60, 'type': 'CNAME', 'value': 'middle.unit.tests.'},
        )
        zone.add_record(record)
        record = Record.new(
            zone,
            'middle',
            {'ttl': 60, 'type': 'CNAME', 'value': 'loop.unit.tests.'},
        )
        zone.add_record(record)
        record = Record.new(
            zone,
            'loop',
            {'ttl': 60, 'type': 'CNAME', 'value': 'start.unit.tests.'},
        )
        zone.add_record(record)

        with TemporaryDirectory() as td:
            # Add some subdirs to make sure that it can create them
            directory = path.join(td.dirname, 'sub', 'dir')
            hosts_file = path.join(directory, 'unit.tests.hosts')
            target = EtcHostsProvider('test', directory)

            # We add everything
            plan = target.plan(zone)
            self.assertEqual(len(zone.records), len(plan.changes))
            self.assertFalse(isfile(hosts_file))

            # Now actually do it
            self.assertEqual(len(zone.records), target.apply(plan))
            self.assertTrue(isfile(hosts_file))

            with open(hosts_file) as fh:
                data = fh.read()
                self.assertTrue(
                    '# loop.unit.tests -> start.unit.tests ' '**loop**' in data
                )
                self.assertTrue(
                    '# middle.unit.tests -> loop.unit.tests ' '**loop**' in data
                )
                self.assertTrue(
                    '# start.unit.tests -> middle.unit.tests '
                    '**loop**' in data
                )
