"""Permanent public entry keys, redirects and reserved removals; no I/O."""

from .errors import SchemaError
from .identifiers import ENTRY_ID

FORMAT = 'aussiefy-entry-ids/v1'


def parse_entry_ids(raw, entries):
    if not isinstance(raw, dict) or set(raw) != {'format', 'ids'} or raw['format'] != FORMAT:
        raise SchemaError(f'entry_ids.yaml: expected {FORMAT} with ids')
    ids = raw['ids']
    if not isinstance(ids, dict):
        raise SchemaError('entry_ids.yaml: ids must map permanent IDs to current IDs or null')
    for key, target in ids.items():
        if (not isinstance(key, str) or not ENTRY_ID.fullmatch(key)
                or target is not None and (not isinstance(target, str) or not ENTRY_ID.fullmatch(target))):
            raise SchemaError('entry_ids.yaml: invalid entry ID or target')
        if key in entries and target != key:
            raise SchemaError(f'entry_ids.yaml: reserved ID {key!r} cannot be reused as an entry')
    resolved = {}
    for key in ids:
        seen, target = set(), key
        while target in ids and ids[target] != target:
            if target in seen:
                raise SchemaError(f'entry_ids.yaml: alias cycle from {key!r}')
            seen.add(target)
            target = ids[target]
        if target is not None and target not in entries:
            raise SchemaError(f'entry_ids.yaml: {key!r} has missing target {target!r}; retain an alias or null tombstone')
        resolved[key] = target
    return resolved


def preserve_entry_ids(previous, current):
    """A published key never vanishes; a redirect or tombstone never becomes a new entry."""
    for key, target in previous.items():
        if key not in current:
            raise SchemaError(f'entry_ids.yaml: published ID {key!r} disappeared; retain an alias or null tombstone')
        if target is None and current[key] is not None:
            raise SchemaError(f'entry_ids.yaml: removed ID {key!r} cannot be reused')
        if target != key and current[key] == key:
            raise SchemaError(f'entry_ids.yaml: alias ID {key!r} cannot be reused')
