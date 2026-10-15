"""Local embedding models for lookup and gaps: meaning where character n-grams only see spelling.

By default that's the bundled Aussie model (aussiefy/static.py): small static vectors tuned on the dictionary,
read with the standard library, deterministic. A bigger sentence-transformers model can replace it, installed
and enabled only by explicit commands:

    aussiefy embedder install          # pip-installs PyTorch (CPU build) and sentence-transformers, downloads the model
    aussiefy embedder enable           # use it instead of the bundled model
    aussiefy embedder status
    aussiefy embedder disable | remove
    aussiefy embedder disable bundled  # no model at all: n-grams only (enable bundled to undo)

Nothing here imports torch unless that model is installed AND enabled. `aussiefy gaps` uses the model to guess
the nearest concept for a gap, and `lookup` adds it as an extra match signal. The engine itself only uses one
when asked (`--embedder bundled|local`), so default translations never change.

State lives in $AUSSIEFY_HOME (default ~/.aussiefy): models/<name>/ holds the saved model, config.json says
which model and whether it's enabled, and whether the bundled one is switched off.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import static
from .errors import UserError

DEFAULT_EMBEDDER = "sentence-transformers/all-MiniLM-L6-v2"   # about 80 MB, fast on CPU
TORCH_INDEXES = {
    "cpu": ["--index-url", "https://download.pytorch.org/whl/cpu"],   # CPU-only build: ~200 MB download, ~1.3 GB installed
    "pypi": [],                                                       # PyPI's default build (CUDA on Linux, GBs)
}


def home() -> Path:
    return Path(os.environ.get("AUSSIEFY_HOME") or Path.home() / ".aussiefy")


def _config_path() -> Path:
    return home() / "config.json"


def load_config() -> dict[str, Any]:
    path = _config_path()
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except ValueError as exc:   # never read a corrupt config as empty: the next save would overwrite it
        raise UserError(f"{path} is not valid JSON ({exc}); fix it or delete it") from exc
    if not (isinstance(cfg, dict) and isinstance(cfg.get("embedder", {}), dict)
            and isinstance(cfg.get("bundled", True), bool)):
        raise UserError(f'{path} should be a JSON object like {{"bundled": true, "embedder": {{"model": ..., '
                        f'"path": ..., "enabled": ...}}}}; fix it or delete it')
    for key, kind in (("enabled", bool), ("path", str), ("model", str)):
        if key in cfg.get("embedder", {}) and not isinstance(cfg["embedder"][key], kind):
            raise UserError(f"{path}: embedder.{key} must be {kind.__name__}; fix it or delete it")
    if cfg.get("embedder") and any(not cfg["embedder"].get(key) for key in ("path", "model")):
        raise UserError(f"{path}: a saved embedder needs a non-empty model and path; fix it or delete it")
    return cfg


def _save_config(cfg: dict[str, Any]) -> None:
    _config_path().parent.mkdir(parents=True, exist_ok=True)
    _config_path().write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def _model_dir(name: str) -> Path:
    return home() / "models" / name.replace("/", "__")


def packages_available() -> bool:
    return all(importlib.util.find_spec(p) is not None for p in ("torch", "sentence_transformers"))


def bundled_enabled() -> bool:
    return static.available() and load_config().get("bundled", True) is not False


def set_bundled(on: bool) -> dict[str, Any]:
    cfg = load_config()
    cfg["bundled"] = on
    _save_config(cfg)
    return status()


def status() -> dict[str, Any]:
    cfg = load_config().get("embedder", {})
    path = Path(cfg["path"]) if cfg.get("path") else None
    b = static.bundled() if static.available() else None
    active = ("local:" + cfg["model"]) if usable() else (b.name if b and bundled_enabled() else "ngram")
    return {
        "active": active,
        "bundled": {"name": b.name if b else None, "enabled": bundled_enabled(),
                    "stale": b.stale() if b else None},
        "home": str(home()),
        "model": cfg.get("model"),
        "path": str(path) if path else None,
        "model_installed": bool(path and path.is_dir()),
        "packages_installed": packages_available(),
        "enabled": bool(cfg.get("enabled")),
        "usable": usable(),
    }


def usable() -> bool:
    """Installed, set up and enabled. Checks files and packages without importing torch."""
    cfg = load_config().get("embedder", {})
    return bool(cfg.get("enabled") and cfg.get("path") and Path(cfg["path"]).is_dir() and packages_available())


def _run(cmd: list[str], dry_run: bool, log) -> None:
    log("$ " + " ".join(cmd))
    if not dry_run:
        subprocess.run(cmd, check=True)


def install(model: str = DEFAULT_EMBEDDER, torch: str = "cpu", from_path: str | None = None, enable: bool = False,
            dry_run: bool = False, log=print) -> dict[str, Any]:
    """Explicitly install PyTorch, sentence-transformers and a model. `torch`: cpu, pypi or skip (already
    installed). `from_path`: a saved sentence-transformers model folder to copy instead of downloading (for
    offline or air-gapped machines)."""
    if from_path and not Path(from_path).is_dir():   # before the pip steps, not after them
        raise UserError(f"--from: no such model folder: {from_path}")
    pip = [sys.executable, "-m", "pip", "install"]
    if torch != "skip":
        if torch not in TORCH_INDEXES:
            raise UserError(f"--torch must be one of {', '.join(TORCH_INDEXES)} or skip")
        _run(pip + ["torch"] + TORCH_INDEXES[torch], dry_run, log)
    _run(pip + ["sentence-transformers>=3"], dry_run, log)

    target = _model_dir(model if not from_path else Path(from_path).name)
    if from_path:
        log(f"copy {from_path} -> {target}")
        if not dry_run:
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(from_path, target)
    else:
        log(f"download {model} -> {target}")
        if not dry_run:
            from sentence_transformers import SentenceTransformer

            try:
                SentenceTransformer(model).save(str(target))
            except Exception as exc:  # network policy, proxy, no such model: say what to do instead
                raise UserError(f"couldn't download {model} ({type(exc).__name__}: {str(exc)[:120]}). The "
                                   "packages are installed; if huggingface.co is blocked here, save the model on "
                                   "another machine and run: aussiefy embedder install --torch skip --from PATH") from exc
    if dry_run:
        return {"dry_run": True, "path": str(target)}

    # prove it loads and embeds before we record it
    from sentence_transformers import SentenceTransformer

    dims = len(SentenceTransformer(str(target)).encode("fair dinkum"))
    cfg = load_config()
    cfg["embedder"] = {"model": model if not from_path else target.name, "path": str(target),
                       "enabled": enable, "dims": dims}
    _save_config(cfg)
    log(f"installed: {dims}-dimension embeddings from {target}" + ("; enabled" if enable else
        "; not enabled yet (run: aussiefy embedder enable)"))
    return status()


def set_enabled(on: bool) -> dict[str, Any]:
    cfg = load_config()
    emb = cfg.get("embedder")
    if on and not (emb and Path(emb.get("path", "")).is_dir()):
        raise UserError("no model installed; run: aussiefy embedder install")
    if emb:
        emb["enabled"] = on
        _save_config(cfg)
    return status()


def remove() -> dict[str, Any]:
    """Delete the saved model and its config. The pip packages stay; the result says how to remove them."""
    cfg = load_config()
    emb = cfg.pop("embedder", None)
    if emb and emb.get("path") and Path(emb["path"]).is_dir():
        shutil.rmtree(emb["path"])
    _save_config(cfg)
    return {**status(), "note": "packages kept; to remove them: pip uninstall sentence-transformers torch"}


_cached = None


def local_embedder():
    """The model lookup and gaps should use: the installed sentence-transformers model if it's installed, set up
    and enabled; otherwise the bundled static model unless it's switched off; otherwise None (n-grams only)."""
    if not usable():
        return static.bundled() if bundled_enabled() else None
    return installed_embedder()


def installed_embedder():
    """The installed sentence-transformers model, which must be installed, set up and enabled. Lazy: torch is
    imported on first use, never at import time."""
    global _cached
    if not usable():
        raise UserError("no local model in use: run `aussiefy embedder install`, then `aussiefy embedder enable`")
    if _cached is None:
        os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")   # keep CLI output clean
        os.environ.setdefault("HF_HUB_OFFLINE", "1")                 # the model is local; never phone home
        from transformers.utils import logging as hf_logging

        hf_logging.disable_progress_bar()
        hf_logging.set_verbosity_error()
        from .embed import SentenceTransformerEmbedder

        _cached = SentenceTransformerEmbedder(load_config()["embedder"]["path"])
        _cached.name = "local:" + load_config()["embedder"]["model"]
    return _cached
