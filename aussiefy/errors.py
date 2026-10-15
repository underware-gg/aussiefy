"""The errors aussiefy raises on purpose. Anything else is a bug and should surface as one."""


class UserError(Exception):
    """A problem the user can fix: a bad dictionary, setting or argument. The message says what and how; the
    CLI prints it and exits 2."""
