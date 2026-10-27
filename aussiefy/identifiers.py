"""Canonical dictionary identifiers, independent of their source file."""

import re

NAMESPACE = r"[a-z][a-z0-9-]*"
ENTRY_ID = re.compile(rf"(?:{NAMESPACE}:)?[a-z0-9][a-z0-9-]*")
CONCEPT_ID = re.compile(rf"(?:{NAMESPACE}:)?[A-Z][A-Z0-9_]*")


def in_namespace(identifier: str, namespace: str) -> bool:
    return isinstance(identifier, str) and identifier.startswith(namespace + ":")
