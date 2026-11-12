"""The errors aussiefy raises on purpose. Anything else is a bug and should surface as one."""


class UserError(Exception):
    """A problem the user can fix: a bad dictionary, setting or argument. The message says what and how; the
    CLI prints it and exits 2."""


class SchemaError(UserError):
    """Dictionary data fails validation."""


class WarningMessage(str):
    """A warning remains a string; its stable diagnostic code is available to a host."""
    code: str

    def __new__(cls, message: str, *, code: str = "engine_warning"):
        value = super().__new__(cls, message)
        value.code = code
        return value


def warning_details(warnings):
    return [{"code": getattr(message, "code", "engine_warning"), "message": str(message)} for message in warnings]
