import copy
import json
import shutil
from types import SimpleNamespace

import pytest

from aussiefy import Translator, load_dictionary
from aussiefy.loader import DATA_DIR


@pytest.fixture(scope="session")
def dictionary():
    return load_dictionary()


@pytest.fixture(scope="session")
def translator(dictionary):
    return Translator(dictionary)


@pytest.fixture(autouse=True)
def _no_local_model(tmp_path_factory, monkeypatch):
    """Tests never see the developer's own installed model or settings (aussiefy embedder install --enable): they
    would make lookup and gaps results depend on the machine, and load torch. The bundled model stays in use."""
    monkeypatch.setenv("AUSSIEFY_HOME", str(tmp_path_factory.mktemp("aussiefy-home")))


@pytest.fixture
def data_copy(tmp_path):
    """A scratch copy of the bundled data directory, for tests that write to the dictionary."""
    data = tmp_path / "data"
    shutil.copytree(DATA_DIR, data)
    return data


@pytest.fixture
def api_error(monkeypatch):
    """An SDK whose calls can fail the way the real one does: tests raise the returned anthropic.APIError."""
    import sys
    import types

    sdk = types.ModuleType("anthropic")

    class APIError(Exception):
        pass

    sdk.APIError = APIError
    monkeypatch.setitem(sys.modules, "anthropic", sdk)
    return APIError


# --- a scripted Claude, at the one seam aussiefy uses (claude.py: client.beta.messages.create) -------------------

class FakeClaude:
    """Each call records a copy of its keyword arguments and returns the next scripted reply, or raises it if it is
    an exception. A call with no reply left fails the test, so FakeClaude() asserts that nothing calls Claude."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls: list[dict] = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))   # callers keep appending to the messages they sent
        if not self.replies:
            raise AssertionError("unexpected call to Claude")
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return reply

    @property
    def kwargs(self) -> dict:
        """The last call's arguments."""
        return self.calls[-1]


def reply(*blocks, stop: str = "end_turn"):
    """A Messages API response with these content blocks."""
    return SimpleNamespace(stop_reason=stop, content=list(blocks))


def text_block(text: str):
    return SimpleNamespace(type="text", text=text)


def json_reply(obj, stop: str = "end_turn"):
    """A schema-constrained reply carrying obj as JSON."""
    return reply(text_block(json.dumps(obj)), stop=stop)


def tool_use(i: int, name: str, **inputs):
    """A tool_use turn calling one tool."""
    return reply(SimpleNamespace(type="tool_use", id=f"t{i}", name=name, input=inputs), stop="tool_use")
