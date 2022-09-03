#
#
#

from collections import defaultdict
from os import makedirs, path
from os.path import isdir
from logging import getLogger
import re

from octodns.provider.base import BaseProvider

__VERSION__ = '0.0.2'


def _wildcard_match(fqdn, wildcards):
    for _, _, regex, record in wildcards:
        if regex.match(fqdn):
            return record
    return None


class EtcHostsProvider(BaseProvider):
    SUPPORTS_GEO = False
    SUPPORTS_DYNAMIC = False
    SUPPORTS = set(('A', 'AAAA', 'ALIAS', 'CNAME'))

    def __init__(self, id, directory, *args, **kwargs):
        self.log = getLogger(f'EtcHostsProvider[{id}]')
        self.log.debug('__init__: id=%s, directory=%s', id, directory)
        super(EtcHostsProvider, self).__init__(id, *args, **kwargs)
        self.directory = directory

        self._expected_zones = set()
        self._records = defaultdict(list)
        self._wildcards = []
        self._zones = []

        self._a_values = {}
        self._aaaa_values = {}
        self._cname_values = {}
        self._a_wildcards = []
        self._aaaa_wildcards = []
        self._cname_wildcards = []

    def populate(self, zone, target=False, lenient=False):
        self.log.debug(
            'populate: name=%s, target=%s, lenient=%s',
            zone.name,
            target,
            lenient,
        )

        self._expected_zones.add(zone.name)

        # We never act as a source, at least for now, if/when we do we still
        # need to noop `if target`
        return False

    def _write(self):
        if not isdir(self.directory):
            makedirs(self.directory)

        # Resolve all the records
        for zone in self._zones:
            name = zone.name
            filepath = path.join(self.directory, name)
            filename = f'{filepath}hosts'
            self.log.info('_apply: filename=%s', filename)
            with open(filename, 'w') as fh:
                fh.write(
                    '###############################################' '###\n'
                )
                fh.write(f'# octoDNS {self.id} {name}\n')
                fh.write(
                    '###############################################' '###\n\n'
                )

                seen = set()
                for record in sorted(zone.records):
                    # Ignore AAAAs when we've seen an A with the same fqdn
                    fqdn = record.fqdn
                    if fqdn in seen:
                        continue
                    seen.add(fqdn)

                    # Follow any symlinks
                    current = record
                    stack = [current]
                    looped = False
                    while current and current._type in ('ALIAS', 'CNAME'):
                        value = current.value
                        try:
                            current = self._records[value][0]
                        except (IndexError, KeyError):
                            # No exact match, look for wildcards
                            current = _wildcard_match(value, self._wildcards)

                        if current:
                            if current in stack:
                                # Loop, break...
                                looped = True
                                break
                            stack.append(current)

                    # Walk the stack/path
                    for node in stack:
                        if node._type in ('ALIAS', 'CNAME'):
                            fh.write(f'# {node.fqdn} -> {node.value}\n')
                    # `node` will be the last element in the stack

                    if looped:
                        # We detected a loop, indicate it
                        fh.write('# ** loop detected **\n')
                    elif node._type in ('ALIAS', 'CNAME'):
                        # We didn't make it all the way to an A/AAAA
                        fh.write('# ** unavailable **\n')
                    elif fqdn[0] == '*':
                        # the record is a wildcard, just add a comment with
                        # info about it
                        fh.write(f'# {node.values[0]} -> {fqdn}\n')
                        fh.write('# ** wildcard **\n')
                    elif node.fqdn[0] == '*':
                        # The last node is a wildcard, note that in a commend
                        # and print the value
                        fh.write(f'# {node.fqdn}\n')
                        fh.write(f'{node.values[0]}\t{fqdn}\n')
                    else:
                        # The last node is a value node, just print it
                        fh.write(f'{node.values[0]}\t{fqdn}\n')

                    fh.write('\n')

        return

    def _apply(self, plan):
        # Store the zone with its records
        desired = plan.desired
        name = desired.name

        self.log.debug(
            '_apply: zone=%s, num_records=%d', name, len(plan.changes)
        )

        # Store it
        self._zones.append(desired)

        # Add all of its records to our maps
        for record in desired.records:
            fqdn = record.fqdn
            if fqdn[0] == '*':
                regex = fqdn.replace('.', '\\.')
                regex = re.compile(rf'^.{regex}$')
                # We want longest match first, preferring A over AAAA so we'll
                # prepend some bits to sort by here, the `-` is to reverse
                # length and still allow type/the sort to be reverse=False
                n = 1024 - len(fqdn)
                self._wildcards.append((n, record._type, regex, record))
            else:
                self._records[fqdn].append(record)

        # Mark it as seen
        try:
            self._expected_zones.remove(name)
        except KeyError:
            pass

        if not self._expected_zones:
            # We've seen everything and we're ready to write out our data
            self.log.debug('_apply: all zone data collected')

            # Sort A before AAAA, as we prefer A when available. CNAME should
            # always stand alone
            for records in self._records.values():
                records.sort(key=lambda r: r._type)

            # Sort wildcards longest first so that we match most specific
            self._wildcards.sort()

            self._write()

        return True
