"""Generate notices and check the provenance of tracked, bundled and reference material.

    python scripts/notices.py generate
    python scripts/notices.py check
    python scripts/notices.py check --wheel   # promotion: build and inspect an isolated wheel

Checks use Git's tracked paths and current file contents. Stage new declarations/files before checking;
ignored local texts are never read. Promotion runs this against its exact committed checkout.
"""

from __future__ import annotations

import argparse
from email import message_from_bytes
from fnmatch import fnmatchcase
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile, BadZipFile

import yaml

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10; declared in the dev extra
    import tomli as tomllib

TEXT_ROOTS = ("tests/corpus/", "tests/fixtures/", "research/")
TEXT_SUFFIXES = {".txt", ".html", ".md", ".mdx"}
RESEARCH_SUFFIXES = TEXT_SUFFIXES | {".json", ".jsonl", ".yaml"}
MODEL_META = "aussiefy/data/model/meta.json"
MODEL_FIELDS = {"name", "version", "recipe.base.model", "recipe.base.revision"}
NOTICES = "THIRD_PARTY_NOTICES.md"


class NoticeError(Exception):
    """A declaration, tracked artefact or built distribution failed its provenance check."""


def _mapping(value, where: str) -> dict:
    if not isinstance(value, dict):
        raise NoticeError(f"{where}: expected a mapping")
    return value


def _rows(value, where: str) -> list[dict]:
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise NoticeError(f"{where}: expected a list of mappings")
    return value


def _text(value, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NoticeError(f"{where}: expected non-empty text")
    return value


def _strings(value, where: str) -> list[str]:
    if not isinstance(value, list):
        raise NoticeError(f"{where}: expected a list of strings")
    return [_text(item, where) for item in value]


def _relative(value, where: str, *, glob: bool = False) -> str:
    value = _text(value, where)
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or path.as_posix() != value:
        raise NoticeError(f"{where}: expected a normalised repository-relative path, got {value!r}")
    if not glob and any(c in value for c in "*?["):
        raise NoticeError(f"{where}: a literal path is required, got {value!r}")
    return value


def _file(root: Path, name: str) -> Path:
    path = root / _relative(name, name)
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise NoticeError(f"{name}: provenance inputs must be ordinary files inside the repository")
    if not path.is_file():
        raise NoticeError(f"{name}: missing ordinary file")
    return path


def _read(root: Path, name: str) -> bytes:
    try:
        return _file(root, name).read_bytes()
    except OSError as exc:
        raise NoticeError(f"{name}: could not read: {exc}") from exc


def _yaml(root: Path, name: str):
    try:
        return yaml.safe_load(_read(root, name).decode("utf-8"))
    except (yaml.YAMLError, UnicodeError) as exc:
        raise NoticeError(f"{name}: invalid UTF-8 YAML: {exc}") from exc


def tracked_files(root: Path) -> set[str]:
    proc = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True)
    if proc.returncode:
        raise NoticeError(f"git ls-files failed: {proc.stderr.decode(errors='replace').strip()}")
    return set(proc.stdout.decode("utf-8").rstrip("\0").split("\0")) - {""}


def remote_specs(texts: dict) -> list[tuple[str, str | None, str]]:
    """Remote rows are either a whole YAML list or a named collection in a page manifest."""
    specs = texts.get("remote_manifests")
    if not isinstance(specs, list):
        raise NoticeError("texts.remote_manifests: expected a list")
    result = []
    for spec in specs:
        if isinstance(spec, str):
            result.append((_relative(spec, "remote manifest"), None, "name"))
        else:
            spec = _mapping(spec, "remote manifest")
            result.append((_relative(spec.get("file"), "remote manifest.file"),
                           _text(spec.get("rows"), "remote manifest.rows"),
                           _text(spec.get("name_field", "name"), "remote manifest.name_field")))
    return result


def _matches(path: str, pattern: str) -> bool:
    """Globs match path components, not across slashes; ** includes zero or more components."""
    parts, pats = PurePosixPath(path).parts, PurePosixPath(pattern).parts
    def match(i: int, j: int) -> bool:
        if j == len(pats):
            return i == len(parts)
        if pats[j] == "**":
            return match(i, j + 1) or (i < len(parts) and match(i + 1, j))
        return i < len(parts) and fnmatchcase(parts[i], pats[j]) and match(i + 1, j + 1)

    return match(0, 0)


def package_files(paths: set[str], project: dict) -> set[str]:
    tool = _mapping(project.get("tool"), "pyproject.toml: tool")
    config = _mapping(tool.get("setuptools"), "pyproject.toml: tool.setuptools")
    packages_config = _mapping(config.get("packages"), "pyproject.toml: packages")
    find = _mapping(packages_config.get("find"), "pyproject.toml: packages.find")
    if find.get("where", ["."]) != ["."]:
        raise NoticeError("pyproject.toml: provenance checking supports packages.find.where = ['.'] only")
    if type(find.get("namespaces", True)) is not bool:
        raise NoticeError("pyproject.toml: packages.find.namespaces must be a boolean")
    includes = _strings(find.get("include", ["*"]), "packages.find.include")
    excludes = _strings(find.get("exclude", []), "packages.find.exclude")
    dirs = {parent.as_posix() for path in paths for parent in PurePosixPath(path).parents if str(parent) != "."}
    packages = {d for d in dirs if any(fnmatchcase(d.replace("/", "."), g) for g in includes) and
                not any(fnmatchcase(d.replace("/", "."), g) for g in excludes) and
                (find.get("namespaces", True) or f"{d}/__init__.py" in paths)}
    result = {p for p in paths if PurePosixPath(p).parent.as_posix() in packages and p.endswith(".py")}
    for package, patterns in _mapping(config.get("package-data", {}), "package-data").items():
        patterns = _strings(patterns, f"package-data.{package}")
        for pattern in patterns:
            _relative(pattern, "package-data pattern", glob=True)
        for directory in packages if package == "*" else {package.replace(".", "/")} & packages:
            result.update(p for p in paths if p.startswith(directory + "/") and
                          any(_matches(p[len(directory) + 1:], g) for g in patterns))
    return result


def _bind(root: Path, binding, errors: list[str], *, model: bool = False) -> dict:
    binding = _mapping(binding, "binds")
    name = _relative(binding.get("file"), "binds.file")
    expect = _mapping(binding.get("expect"), f"{name}: binds.expect")
    if not expect or (model and (name != MODEL_META or not MODEL_FIELDS <= expect.keys())):
        raise NoticeError(f"{name}: declare non-empty metadata bindings (model needs {', '.join(sorted(MODEL_FIELDS))})")
    try:
        actual = json.loads(_read(root, name))
    except (ValueError, UnicodeError) as exc:
        raise NoticeError(f"{name}: invalid JSON: {exc}") from exc
    actual = _mapping(actual, name)
    for key, expected in expect.items():
        _text(expected, f"{name}: expected {key}")
        value = actual
        for part in _text(key, "binds.expect key").split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if value != expected:
            errors.append(f"{name}: {key} is {value!r}, expected {expected!r}; review and update third_party.yaml")
    return actual


def _claims(root: Path, registry: dict, paths: set[str], errors: list[str]) -> dict[str, list[str]]:
    claims: dict[str, list[str]] = {}

    def claim(path: str, owner: str):
        claims.setdefault(path, []).append(owner)
        if path not in paths:
            errors.append(f"{path}: declared by {owner} but not tracked")

    for item in _rows(registry.get("first_party"), "first_party"):
        pattern = _relative(item.get("glob"), "first_party.glob", glob=True)
        _text(item.get("reason"), f"first_party {pattern}: reason")
        excludes = [_relative(g, f"first_party {pattern}: exclude", glob=True)
                    for g in _strings(item.get("exclude", []), f"first_party {pattern}: exclude")]
        for path in sorted(paths):
            if _matches(path, pattern) and not any(_matches(path, g) for g in excludes):
                claim(path, f"first-party {pattern}")
    components = _rows(registry.get("components"), "components")
    ids = set()
    model_metadata = None
    for component in components:
        ident = _text(component.get("id"), "component.id")
        if ident in ids:
            raise NoticeError(f"components: duplicate id {ident}")
        ids.add(ident)
        files = _strings(component.get("paths"), f"{ident}.paths")
        if not files:
            raise NoticeError(f"{ident}: declare at least one bundled path")
        for path in files:
            claim(_relative(path, f"{ident}.paths"), ident)
        for path, digest in _mapping(component.get("digests", {}), f"{ident}.digests").items():
            if path not in files:
                raise NoticeError(f"{ident}: digest path must belong to the component: {path}")
            _check_digest(root, path, digest, errors)
        metadata = _bind(root, component.get("binds"), errors, model=any(p.startswith("aussiefy/data/model/") for p in files))
        if component["binds"]["file"] == MODEL_META:
            model_metadata = metadata
    credits = _rows(registry.get("credits"), "credits")
    for credit in credits:
        _text(credit.get("name"), "credit.name")
        _text(credit.get("copyright"), "credit.copyright")
        _text(credit.get("url"), "credit.url")
        _bind(root, credit.get("binds"), errors)
    for ident, spec in _mapping(registry.get("corpus_licences", {}), "corpus_licences").items():
        spec = _mapping(spec, f"corpus_licences.{ident}")
        path = _relative(spec.get("file"), f"corpus_licences.{ident}.file")
        _text(spec.get("url"), f"corpus_licences.{ident}.url")
        _check_digest(root, path, spec.get("sha256"), errors)
        claim(path, f"corpus licence {ident}")
    if model_metadata and model_metadata.get("wordnet"):
        wordnet = _text(model_metadata["wordnet"], f"{MODEL_META}: wordnet")
        matches = [c for c in credits if c["name"] == wordnet and c["binds"]["file"] == MODEL_META and
                   c["binds"]["expect"].get("wordnet") == wordnet]
        if len(matches) != 1:
            errors.append(f"{MODEL_META}: declare exactly one {wordnet} credit bound to the wordnet metadata field")

    texts = _mapping(registry.get("texts"), "texts")
    remote_names = set()
    excerpts = set()
    for name, collection, name_field in remote_specs(texts):
        data = _yaml(root, name)
        if collection:
            data = _mapping(data, name).get(collection)
        for row in _rows(data, name):
            work = _text(row.get(name_field), f"{name}: {name_field}")
            if name_field == "file":
                work = PurePosixPath(_relative(work, f"{name}: file")).stem
            if work in remote_names:
                raise NoticeError(f"{name}: duplicate remote work {work}")
            remote_names.add(work)
            for excerpt in _rows(row.get("excerpts"), f"{name}:{work}: excerpts (use [] for remote-only works)"):
                path = _relative(excerpt.get("file"), f"{work}: excerpt.file")
                notice = _text(excerpt.get("notice"), f"{path}: excerpt.notice")
                cap = excerpt.get("max_words")
                if type(cap) is not int or cap < 1:
                    raise NoticeError(f"{path}: excerpt.max_words must be a positive integer")
                claim(path, f"excerpt of {work}")
                excerpts.add(path)
                content = _read(root, path).decode("utf-8")
                if not content.startswith(notice.rstrip("\n") + "\n\n"):
                    errors.append(f"{path}: required excerpt notice header is missing or changed")
                if len(content.split()) > cap:
                    errors.append(f"{path}: excerpt exceeds {cap} words (including notice header)")
    for spec in _rows(texts.get("manifests"), "texts.manifests"):
        name = _relative(spec.get("file"), "manifest.file")
        directory = _relative(spec.get("dir"), "manifest.dir")
        required = _strings(spec.get("require"), f"{name}: require")
        for row in _rows(_yaml(root, name), name):
            if "file" not in row:
                raise NoticeError(f"{name}: each provenance row must declare file (null only for remote works)")
            for field in required:
                _text(row.get(field), f"{name}: {row.get('file')}: {field}")
            if row.get("file") is None:
                remote = _text(row.get("remote"), f"{name}: remote")
                if row.get("status") != "copyright" or remote not in remote_names:
                    raise NoticeError(f"{name}: file:null must name a declared copyrighted remote work")
                continue
            path = f"{directory}/{_relative(row['file'], name + ': file')}"
            claim(path, name)
    research = texts.get("research")
    if research is not None:
        name = _relative(_mapping(research, "texts.research").get("file"), "texts.research.file")
        for row in _rows(_mapping(_yaml(root, name), name).get("derived"), name + ': derived'):
            sources = row.get("sources") if "sources" in row else [row.get("source")]
            sources = [_relative(source, name + ': source') for source in _strings(sources, name + ': sources')]
            if not sources or len(sources) != len(set(sources)):
                raise NoticeError(f"{name}: derived sources must be a non-empty unique list")
            for source in sources:
                if not source.startswith("tests/corpus/") or source.startswith("tests/corpus/local/") or len(claims.get(source, [])) != 1:
                    errors.append(f"{name}: derived source needs exactly one redistributable corpus claim: {source}")
            _text(row.get("modifications"), name + ': modifications')
            for pattern in _strings(row.get("paths"), name + ': paths'):
                pattern = _relative(pattern, name + ': path', glob=True)
                if not pattern.startswith("research/"):
                    raise NoticeError(f"{name}: derived paths must be research paths")
                matches = sorted(path for path in paths if _matches(path, pattern))
                if not matches:
                    errors.append(f"{name}: derived pattern has no tracked files: {pattern}")
                for path in matches:
                    claim(path, f"{name}: inherits {', '.join(sources)}")
    local = _relative(texts.get("local_dir"), "texts.local_dir")
    for path in sorted(paths):
        if path.startswith(local + "/") and path != f"{local}/README.md":
            errors.append(f"{path}: local-only content must not be tracked")
        if PurePosixPath(path).stem in remote_names and path not in excerpts:
            errors.append(f"{path}: undeclared tracked file named for a remote-only work")
    return claims


def _licences(root: Path, registry: dict, project: dict, paths: set[str], errors: list[str]) -> set[str]:
    licences = _mapping(registry.get("licences"), "licences")
    for ident in licences:
        _text(ident, "licences: identifier")
    own = _mapping(registry.get("project_licence"), "project_licence")
    own_ident = _text(own.get("licence"), "project_licence.licence")
    own_file = _relative(own.get("file"), "project_licence.file")
    used = {own_ident}
    for item in registry["components"]:
        used.add(_text(item.get("licence"), "component.licence"))
        _text(item.get("name"), "component.name")
        _text(item.get("modifications"), f"{item['id']}: modifications")
        upstreams = _rows(item.get("upstream"), f"{item['id']}: upstream")
        base = item["binds"]["expect"].get("recipe.base.model")
        if not upstreams or (base and not any(s.get("name") == base for s in upstreams)):
            errors.append(f"{item['id']}: upstream evidence must include the bound base model")
        for upstream in upstreams:
            for key in ("name", "url", "licence", "copyright"):
                _text(upstream.get(key), f"{item['id']}: upstream.{key}")
            used.add(upstream["licence"])
    if used != set(licences):
        errors.append(f"third_party.yaml: licence declarations differ from used identifiers: {sorted(used ^ licences.keys())}")
    files = {own_file, NOTICES}
    _check_digest(root, own_file, own.get("sha256"), errors)
    for ident, spec in licences.items():
        spec = _mapping(spec, f"licences.{ident}")
        name = _relative(spec.get("file"), f"licences.{ident}.file")
        if name != f"LICENSES/{ident}.txt":
            raise NoticeError(f"{ident}: canonical text must be LICENSES/{ident}.txt")
        _text(spec.get("url"), f"{name}: evidence URL")
        _check_digest(root, name, spec.get("sha256"), errors)
        files.add(name)
    expression = _text(project["project"].get("license"), "project.license")
    if not re.fullmatch(r"[A-Za-z0-9.-]+(?: AND [A-Za-z0-9.-]+)*", expression):
        raise NoticeError("project.license: this gate supports an AND expression of declared identifiers")
    if set(expression.split(" AND ")) != used:
        errors.append(f"pyproject.toml: project.license must cover {', '.join(sorted(used))}")
    patterns = _strings(project["project"].get("license-files"), "project.license-files")
    selected = {p for p in paths for g in patterns if _matches(p, _relative(g, "license-files", glob=True))}
    if selected != files:
        errors.append(f"pyproject.toml: license-files mismatch: missing {sorted(files - selected)}, extra {sorted(selected - files)}")
    for name in sorted(files - paths):
        errors.append(f"{name}: licence/notice file is not tracked")
    return files


def _check_digest(root: Path, name: str, value, errors: list[str]) -> None:
    digest = _text(value, f"{name}: sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise NoticeError(f"{name}: sha256 must be 64 lowercase hex characters")
    if hashlib.sha256(_read(root, name)).hexdigest() != digest:
        errors.append(f"{name}: reviewed licence text changed; restore it or review its evidence and digest")


def _scraped(root: Path, errors: list[str]) -> None:
    from aussiefy.errors import UserError
    from aussiefy.scrape.fetch import reference_only
    from urllib.parse import urlsplit

    name = "aussiefy/data/entries/scraped.yaml"
    overlays = _mapping(_yaml(root, "aussiefy/data/sources.yaml"), "sources.yaml")
    for row in _rows(_yaml(root, name), name):
        ident = _text(row.get("id"), f"{name}: id")
        urls = _strings(row.get("sources"), f"{name}:{ident}: sources")
        if not urls:
            errors.append(f"{name}:{ident}: scraped entries must name a source URL")
        for url in urls + _strings(overlays.get(ident, []), f"sources.yaml:{ident}"):
            try:
                parsed = urlsplit(url)
                host = parsed.hostname
            except ValueError as exc:
                raise NoticeError(f"{name}:{ident}: malformed source URL: {url!r}") from exc
            if parsed.scheme not in ("http", "https") or not host:
                errors.append(f"{name}:{ident}: source must be an HTTP(S) URL: {url!r}")
            else:
                try:
                    reason = reference_only(url, data_dir=root / "aussiefy/data")
                except UserError as exc:
                    raise NoticeError(str(exc)) from exc
                if reason:
                    errors.append(f"{name}:{ident}: reference-only source must not be scraped: {url}")


def render(registry: dict) -> str:
    own = registry["project_licence"]
    lines = ["# Third-party notices", "", "<!-- Generated by scripts/notices.py. Edit third_party.yaml, then regenerate. -->",
             "", f"aussiefy's own code and data are under {own['licence']} (see [LICENSE]({own['file']})). Bundled third-party material",
             "keeps its own licences; canonical texts are in [LICENSES/](LICENSES/).", ""]
    for item in registry["components"]:
        lines += [f"## {item['name']}", "", "Bundled files: " + ", ".join(f"`{p}`" for p in item["paths"]) + ".", ""]
        pins = item["binds"]["expect"]
        lines += ["Reviewed metadata: " + "; ".join(f"`{key}` = `{value}`" for key, value in sorted(pins.items())) + ".", ""]
        for source in item["upstream"]:
            ident = source["licence"]
            lines += [f"- [{source['name']}]({source['url']}): {source['copyright']}. "
                      f"[{ident}]({registry['licences'][ident]['file']})."]
        heading = "**Modifications** (Apache-2.0 section 4(b)):" if item["licence"] == "Apache-2.0" else "**Modifications**:"
        lines += ["", heading, "", item["modifications"].strip(), ""]
    lines += ["## Training-only credits", ""]
    for credit in registry["credits"]:
        lines += [f"{credit['name']} was used in training; its database is not distributed.", "",
                  f"{credit['copyright']} [Licence]({credit['url']}).", ""]
    lines += ["## Reference text provenance", "", "The corpus and research texts do not ship in the wheel. Their provenance declarations are:", ""]
    for spec in registry["texts"]["manifests"]:
        lines += [f"- [{spec['file']}]({spec['file']})"]
    if registry["texts"].get("research"):
        name = registry["texts"]["research"]["file"]
        lines += [f"- [{name}]({name}): originals and adapted research artefacts retain their source's licence and attribution; modification declarations accompany each group."]
    if registry.get("corpus_licences"):
        lines += ["", "Interfold corpus and its research adaptations retain Copyright The Interfold contributors and LGPL-3.0-or-later; original pages are verbatim and retellings modify the prose. These materials are not bundled in the wheel."]
        for ident, spec in registry["corpus_licences"].items():
            lines += [f"- [{ident}]({spec['file']})"]
    lines += ["", "Remote-only works and permitted excerpts:", ""]
    for name, _, _ in remote_specs(registry["texts"]):
        lines += [f"- [{name}]({name})"]
    return "\n".join(lines) + "\n"


def validate(root: Path, *, freshness: bool = True) -> tuple[dict, dict, set[str], set[str]]:
    registry = _mapping(_yaml(root, "third_party.yaml"), "third_party.yaml")
    if type(registry.get("schema")) is not int or registry["schema"] != 1:
        raise NoticeError("third_party.yaml: expected schema: 1")
    try:
        project = tomllib.loads(_read(root, "pyproject.toml").decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise NoticeError(f"pyproject.toml: invalid UTF-8 TOML: {exc}") from exc
    _mapping(project.get("project"), "pyproject.toml: project")
    paths = tracked_files(root)
    errors = [f"{p}: required provenance input is not tracked" for p in ("third_party.yaml", "pyproject.toml") if p not in paths]
    claims = _claims(root, registry, paths, errors)
    inputs = {item["binds"]["file"] for item in registry["components"] + registry["credits"]}
    inputs.update(spec["file"] for spec in registry.get("corpus_licences", {}).values())
    if registry["texts"].get("research"):
        inputs.add(registry["texts"]["research"]["file"])
    inputs.update(spec["file"] for spec in registry["texts"]["manifests"])
    inputs.update(name for name, _, _ in remote_specs(registry["texts"]))
    errors.extend(f"{p}: required provenance input is not tracked" for p in sorted(inputs - paths))
    packaged = package_files(paths, project)
    for component in registry["components"]:
        errors.extend(f"{p}: bundled component is not selected by packaging" for p in component["paths"] if p not in packaged)
    needed = packaged | {p for p in paths if p.startswith(TEXT_ROOTS) and PurePosixPath(p).suffix in TEXT_SUFFIXES}
    needed |= {p for p in paths if p.startswith("research/") and PurePosixPath(p).suffix in RESEARCH_SUFFIXES}
    for path in sorted(needed | claims.keys()):
        _file(root, path)
        owners = claims.get(path, [])
        if not owners:
            errors.append(f"{path}: no provenance declaration; add a manifest entry or reviewed first-party claim")
        elif len(owners) != 1:
            errors.append(f"{path}: duplicate provenance claims: {', '.join(owners)}")
    licences = _licences(root, registry, project, paths, errors)
    for name in sorted(licences - ({NOTICES} if not freshness else set())):
        _file(root, name)
    _scraped(root, errors)
    if errors:
        raise NoticeError("\n".join(errors))
    if freshness and _read(root, NOTICES).decode("utf-8") != render(registry):
        raise NoticeError(f"{NOTICES}: stale; run python scripts/notices.py generate")
    return registry, project, packaged, licences


def inspect_wheel(root: Path, wheel: Path, project: dict, packaged: set[str], licences: set[str]) -> None:
    try:
        with ZipFile(wheel) as archive:
            names = set(archive.namelist())
            metas = [name for name in names if name.endswith(".dist-info/METADATA")]
            if len(metas) != 1:
                raise NoticeError("wheel: expected exactly one .dist-info/METADATA")
            prefix = metas[0].removesuffix("METADATA")
            metadata = message_from_bytes(archive.read(metas[0]))
            if metadata.get("License-Expression") != project["project"]["license"]:
                raise NoticeError("wheel: License-Expression differs from pyproject.toml")
            if set(metadata.get_all("License-File", [])) != licences:
                raise NoticeError("wheel: License-File declarations differ from reviewed licence files")
            licence_prefix = prefix + "licenses/"
            archived_licences = {name[len(licence_prefix):] for name in names if name.startswith(licence_prefix) and
                                 not name.endswith("/")}
            if archived_licences != licences:
                raise NoticeError("wheel: actual licence file set differs from reviewed licence files")
            shipped = {n for n in names if not n.startswith(prefix) and not n.endswith("/")}
            if shipped != packaged:
                raise NoticeError(f"wheel: packaged files differ: missing {sorted(packaged - shipped)}, extra {sorted(shipped - packaged)}")
            for name in sorted(packaged | licences):
                archived = prefix + "licenses/" + name if name in licences else name
                if archived not in names or archive.read(archived) != _read(root, name):
                    raise NoticeError(f"wheel: missing or changed reviewed content: {name}")
    except (BadZipFile, OSError) as exc:
        raise NoticeError(f"wheel: could not read {wheel.name}: {exc}") from exc


def check(root: Path, *, wheel: bool = False) -> None:
    _, project, packaged, licences = validate(root)
    if not wheel:
        return
    with tempfile.TemporaryDirectory(prefix="aussiefy-wheel-") as temporary:
        source, dist = Path(temporary) / "source", Path(temporary) / "dist"
        source.mkdir()
        for name in sorted(tracked_files(root)):
            original, target = root / name, source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if original.is_symlink():
                target.symlink_to(original.readlink())
            else:
                shutil.copyfile(original, target)
        proc = subprocess.run([sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(dist),
                               str(source)], capture_output=True, text=True)
        if proc.returncode:
            raise NoticeError("wheel build failed (install the dev extra); no release:\n" + (proc.stdout + proc.stderr)[-3000:])
        wheels = list(dist.glob("*.whl"))
        if len(wheels) != 1:
            raise NoticeError("wheel build: expected exactly one wheel")
        inspect_wheel(root, wheels[0], project, packaged, licences)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate", help="validate declarations and regenerate THIRD_PARTY_NOTICES.md")
    checking = sub.add_parser("check", help="check tracked provenance and notices without rewriting them")
    checking.add_argument("--wheel", action="store_true", help="also build/inspect an isolated wheel (dev extra required)")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    try:
        if args.command == "generate":
            registry, _, _, _ = validate(root, freshness=False)
            (root / NOTICES).write_text(render(registry), encoding="utf-8", newline="")
        else:
            check(root, wheel=args.wheel)
    except (NoticeError, UnicodeError) as exc:
        print(f"provenance: {exc}", file=sys.stderr)
        return 2
    print("Third-party notices generated." if args.command == "generate" else "Provenance and licence checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
