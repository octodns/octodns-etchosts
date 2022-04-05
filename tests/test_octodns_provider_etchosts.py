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

        record = Record.new(zone, '', {
            'ttl': 60,
            'type': 'ALIAS',
            'value': 'www.unit.tests.'
        })
        zone.add_record(record)

        record = Record.new(zone, 'www', {
            'ttl': 60,
            'type': 'AAAA',
            'value': '2001:4860:4860::8888',
        })
        zone.add_record(record)
        record = Record.new(zone, 'www', {
            'ttl': 60,
            'type': 'A',
            'values': ['1.1.1.1', '2.2.2.2'],
        })
        zone.add_record(record)

        record = record.new(zone, 'v6', {
            'ttl': 60,
            'type': 'AAAA',
            'value': '2001:4860:4860::8844',
        })
        zone.add_record(record)

        record = record.new(zone, 'start', {
            'ttl': 60,
            'type': 'CNAME',
            'value': 'middle.unit.tests.',
        })
        zone.add_record(record)
        record = record.new(zone, 'middle', {
            'ttl': 60,
            'type': 'CNAME',
            'value': 'unit.tests.',
        })
        zone.add_record(record)

        record = record.new(zone, 'ext', {
            'ttl': 60,
            'type': 'CNAME',
            'value': 'github.com.',
        })
        zone.add_record(record)

        record = record.new(zone, '*', {
            'ttl': 60,
            'type': 'A',
            'value': '3.3.3.3',
        })
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
                self.assertTrue('# unit.tests. -> www.unit.tests.' in data)
                self.assertTrue('1.1.1.1\tunit.tests' in data)

                self.assertTrue('# start.unit.tests. -> middle.unit.tests.' in
                                data)
                self.assertTrue('# middle.unit.tests. -> unit.tests.' in data)
                self.assertTrue('# unit.tests. -> www.unit.tests.' in data)
                self.assertTrue('1.1.1.1	start.unit.tests' in data)

            # second empty run that won't create dirs and overwrites file
            plan = Plan(zone, zone, [], True)
            self.assertEqual(0, target.apply(plan))

    def test_cname_other_zone(self):
        zone = Zone('unit.tests.', [])

        record = Record.new(zone, 'source', {
            'ttl': 60,
            'type': 'CNAME',
            'value': 'target.other.tests.',
        })
        zone.add_record(record)

        other_zone = Zone('other.tests.', [])

        record = Record.new(other_zone, 'target', {
            'ttl': 60,
            'type': 'A',
            'values': ['1.1.1.1', '2.2.2.2'],
        })
        other_zone.add_record(record)

        with TemporaryDirectory() as td:
            # Add some subdirs to make sure that it can create them
            directory = path.join(td.dirname, 'hosts')
            hosts_file = path.join(directory, 'unit.tests.hosts')
            target = EtcHostsProvider('test', directory)

            # We add everything
            plan = target.plan(zone)
            self.assertEqual(len(zone.records), len(plan.changes))
            other_plan = target.plan(other_zone)
            self.assertEqual(len(other_zone.records), len(other_plan.changes))

            self.assertFalse(isfile(hosts_file))

            # Apply the first one, nothing will be written yet
            self.assertEqual(len(zone.records), target.apply(plan))
            self.assertFalse(isfile(hosts_file))
            # Apply the second one, now both will be written
            self.assertEqual(len(other_zone.records), target.apply(other_plan))
            self.assertTrue(isfile(hosts_file))

            with open(hosts_file) as fh:
                data = fh.read()
                # CNAME to other zone
                self.assertTrue('# source.unit.tests. -> target.other.tests.\n'
                                '1.1.1.1\tsource.unit.tests' in data)

    def test_cnames_and_wildcards(self):
        zone = Zone('unit.tests.', [])

        record = Record.new(zone, '*.sub', {
            'ttl': 60,
            'type': 'A',
            'value': '1.2.3.4',
        })
        zone.add_record(record)

        # One that matches a wildcard
        record = Record.new(zone, 'yep', {
            'ttl': 60,
            'type': 'CNAME',
            'value': 'foo.sub.unit.tests.',
        })
        zone.add_record(record)

        # One that doesn't match anything
        record = Record.new(zone, 'nope', {
            'ttl': 60,
            'type': 'CNAME',
            'value': 'foo.not.unit.tests.',
        })
        zone.add_record(record)

        # Wildcard CNAME
        record = Record.new(zone, '*.cname', {
            'ttl': 60,
            'type': 'CNAME',
            'value': 'foo.sub.unit.tests.',
        })
        zone.add_record(record)

        # Something that matches the CNAME wildcard
        record = Record.new(zone, 'yes', {
            'ttl': 60,
            'type': 'CNAME',
            'value': 'foo.cname.unit.tests.',
        })
        zone.add_record(record)

        with TemporaryDirectory() as td:
            # Add some subdirs to make sure that it can create them
            directory = path.join(td.dirname, 'hosts')
            hosts_file = path.join(directory, 'unit.tests.hosts')
            target = EtcHostsProvider('test', directory)

            # We add everything
            plan = target.plan(zone)
            self.assertEqual(len(zone.records), len(plan.changes))
            self.assertFalse(isfile(hosts_file))

            # Apply the first one, nothing will be written yet
            self.assertEqual(len(zone.records), target.apply(plan))
            self.assertTrue(isfile(hosts_file))

            with open(hosts_file) as fh:
                data = fh.read()
                # wildcard is there
                self.assertTrue('# 1.2.3.4 -> *.sub.unit.tests.\n'
                                '# ** wildcard **' in data)
                # CNAME that matches a wildcard
                self.assertTrue('# nope.unit.tests. -> foo.not.unit.tests.\n'
                                '# ** unavailable **' in data)
                # CNAME that matches a wildcard
                self.assertTrue('# yep.unit.tests. -> foo.sub.unit.tests.\n'
                                '# *.sub.unit.tests.\n'
                                '1.2.3.4\tyep.unit.tests' in data)
                # CNAME wildcard
                self.assertTrue('# yes.unit.tests. -> foo.cname.unit.tests.\n'
                                '# *.cname.unit.tests. -> '
                                'foo.sub.unit.tests.\n'
                                '# *.sub.unit.tests.\n'
                                '1.2.3.4\tyes.unit.tests.')

    def test_cname_loop(self):
        source = EtcHostsProvider('test', 'not-used')

        zone = Zone('unit.tests.', [])

        # We never populate anything, when acting as a source
        source.populate(zone, target=source)
        self.assertEqual(0, len(zone.records))
        # Same if we're acting as a target
        source.populate(zone)
        self.assertEqual(0, len(zone.records))

        record = Record.new(zone, 'start', {
            'ttl': 60,
            'type': 'CNAME',
            'value': 'middle.unit.tests.',
        })
        zone.add_record(record)
        record = Record.new(zone, 'middle', {
            'ttl': 60,
            'type': 'CNAME',
            'value': 'loop.unit.tests.',
        })
        zone.add_record(record)
        record = Record.new(zone, 'loop', {
            'ttl': 60,
            'type': 'CNAME',
            'value': 'start.unit.tests.',
        })
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
                self.assertTrue('# loop.unit.tests. -> start.unit.tests.\n'
                                '# ** loop detected **' in data)
                self.assertTrue('# middle.unit.tests. -> loop.unit.tests.\n'
                                '# ** loop detected **' in data)
                self.assertTrue('# start.unit.tests. -> middle.unit.tests.\n'
                                '# ** loop detected **' in data)
