"""Tracked provenance and the contents of a distribution are checked, not inferred from filenames."""

import copy
from email.message import Message
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import notices as n  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


def put(root, path, text):
    dest = root / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


def registry(root):
    return yaml.safe_load((root / "third_party.yaml").read_text())


def save_registry(root, value):
    put(root, "third_party.yaml", yaml.safe_dump(value, sort_keys=False))


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    data = registry(ROOT)
    # Minimal corpus plus a synthetic remote-page fixture for the structured remote policy.
    data["texts"]["remote_manifests"].append({"file": "tests/corpus/everyday/interfold.yaml", "rows": "pages", "name_field": "file"})
    put(root, "research/PROVENANCE.yaml", "derived: []\n")
    for spec in data.get("corpus_licences", {}).values():
        put(root, spec["file"], (ROOT / spec["file"]).read_text())
    for component in data["components"]:
        if component["id"] == "english-pos-tagger":
            for name in component["paths"] + [component["binds"]["file"]]:
                dest = root / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((ROOT / name).read_bytes())
    for spec in data["texts"]["manifests"]:
        put(root, spec["file"], "[]\n")
    for name, collection, _ in n.remote_specs(data["texts"]):
        put(root, name, yaml.safe_dump({collection: []}) if collection else "[]\n")
    for name in ("LICENSE", "LICENSES/MIT.txt", "LICENSES/Apache-2.0.txt", n.MODEL_META,
                 "aussiefy/data/source_policy.yaml", "research/retellings-2026-10-11/harnessed/moloch.txt",
                 "tests/corpus/remote.yaml"):
        put(root, name, (ROOT / name).read_text())
    put(root, "aussiefy/__init__.py", '__version__ = "0.1.0"\n')
    put(root, "aussiefy/data/model/vectors.f16", "fixture vectors")
    put(root, "aussiefy/data/model/vocab.txt", "fixture vocab")
    put(root, "aussiefy/data/entries/scraped.yaml", "[]\n")
    put(root, "aussiefy/data/sources.yaml", "{}\n")
    put(root, "tests/corpus/reference/source.txt", "Own fixture text.\n")
    put(root, "tests/corpus/reference/SOURCES.yaml", yaml.safe_dump([
        {"file": "source.txt", "title": "Fixture", "author": "Test", "licence": "own-work", "notes": "Written for this test."}
    ]))
    put(root, "tests/corpus/classics/manifest.yaml", "[]\n")
    put(root, "pyproject.toml", (ROOT / "pyproject.toml").read_text())
    put(root, "third_party.yaml", yaml.safe_dump(data, sort_keys=False))
    put(root, n.NOTICES, n.render(data))
    put(root, ".gitignore", "tests/corpus/local/*\n!tests/corpus/local/README.md\n")
    git(root, "add", ".")
    return root


def test_repository_provenance_is_current():
    n.check(ROOT)


@pytest.mark.parametrize("manifest,collection,name", [
    ("tests/corpus/everyday/news-remote.yaml", "items", "goodyear_blimp_centennial"),
    ("tests/corpus/everyday/instructions-remote.yaml", "items", "rockwell_transplanting_1911"),
    ("tests/corpus/everyday/interfold.yaml", "pages", "build_quick_start.md"),
])
def test_everyday_remote_rows_forbid_undeclared_tracked_copies(repo, manifest, collection, name):
    row = {"file" if collection == "pages" else "name": name, "excerpts": []}
    put(repo, manifest, yaml.safe_dump({collection: [row]} if collection else [row]))
    stem = Path(name).stem
    path = f"tests/corpus/reference/{stem}.txt"
    put(repo, path, "A purported full remote text.\n")
    git(repo, "add", manifest, path)
    with pytest.raises(n.NoticeError, match="named for a remote-only work"):
        n.check(repo)


@pytest.mark.parametrize("change", ["missing_excerpts", "bad_collection", "untracked", "duplicate_name"])
def test_interfold_remote_declaration_is_checked(repo, change):
    name = "tests/corpus/everyday/interfold.yaml"
    rows = [{"file": "home.md", "excerpts": []}]
    if change == "missing_excerpts":
        rows[0].pop("excerpts")
    elif change == "duplicate_name":
        rows.append(dict(rows[0]))
    put(repo, name, yaml.safe_dump({"pages": False if change == "bad_collection" else rows}))
    if change == "untracked":
        git(repo, "rm", "-f", "--cached", name)
    errors = {"missing_excerpts": "excerpts", "bad_collection": "list of mappings",
              "untracked": "required provenance input is not tracked", "duplicate_name": "duplicate remote work"}
    with pytest.raises(n.NoticeError, match=errors[change]):
        n.check(repo)


def test_valid_fixture_and_notice_generation_are_deterministic(repo):
    n.check(repo)
    data = registry(repo)
    assert n.render(data) == n.render(copy.deepcopy(data)) == (repo / n.NOTICES).read_text()


@pytest.mark.parametrize("path", ["tests/corpus/reference/unlisted.txt", "tests/corpus/reference/unlisted.md",
                                  "tests/fixtures/unlisted.html", "research/new-round/source.txt",
                                  "aussiefy/data/model/extra.bin", "aussiefy/vendor.py"])
def test_new_tracked_material_needs_a_claim(repo, path):
    put(repo, path, "Unclaimed fixture.\n")
    # Python is declared first-party, so a new vendored module needs a component declaration that replaces that claim.
    if path.endswith("vendor.py"):
        data = registry(repo)
        data["first_party"] = [c for c in data["first_party"] if c["glob"] != "aussiefy/**/*.py"]
        data["first_party"].append({"glob": "aussiefy/__init__.py", "reason": "Own fixture code"})
        save_registry(repo, data)
    git(repo, "add", path)
    with pytest.raises(n.NoticeError, match="no provenance declaration"):
        n.check(repo)


def test_ignored_private_content_is_not_read_or_classified(repo):
    put(repo, "tests/corpus/local/moloch.txt", "Uncommitted private fixture")
    (repo / "tests/corpus/local/moloch.txt").chmod(0)
    try:
        n.check(repo)
    finally:
        (repo / "tests/corpus/local/moloch.txt").chmod(0o600)


def test_forced_tracking_of_any_local_file_fails(repo):
    put(repo, "tests/corpus/local/innocent.dat", "Private fixture")
    git(repo, "add", "-f", "tests/corpus/local/innocent.dat")
    with pytest.raises(n.NoticeError, match="local-only content must not be tracked"):
        n.check(repo)


def test_duplicate_claims_fail(repo):
    data = registry(repo)
    data["first_party"].append({"glob": "tests/corpus/reference/source.txt", "reason": "Conflicting own-work claim"})
    save_registry(repo, data)
    with pytest.raises(n.NoticeError, match="duplicate provenance claims"):
        n.check(repo)


@pytest.mark.parametrize("kind", ["missing_file", "missing_licence", "untracked_manifest", "duplicate_row"])
def test_provenance_rows_must_be_complete_and_tracked(repo, kind):
    path = repo / "tests/corpus/reference/SOURCES.yaml"
    rows = yaml.safe_load(path.read_text())
    if kind == "missing_file":
        rows[0]["file"] = "absent.txt"
    elif kind == "missing_licence":
        del rows[0]["licence"]
    elif kind == "duplicate_row":
        rows.append(copy.deepcopy(rows[0]))
    else:
        git(repo, "rm", "--cached", "tests/corpus/reference/SOURCES.yaml")
    path.write_text(yaml.safe_dump(rows))
    with pytest.raises(n.NoticeError):
        n.check(repo)


def test_remote_pointer_name_must_be_text(repo):
    put(repo, "tests/corpus/classics/manifest.yaml", yaml.safe_dump([
        {"file": None, "remote": [], "status": "copyright", "title": "Private", "author": "Test",
         "licence": "copyright", "notes": "Fixture remote pointer"}
    ]))
    with pytest.raises(n.NoticeError, match="remote: expected non-empty text"):
        n.check(repo)


@pytest.mark.parametrize("field,value", [("version", "9.0.0"), ("wordnet", "Different database"),
                                       ("recipe.base.model", "other/model"), ("recipe.base.revision", "new-revision")])
def test_changed_model_requires_reviewed_declaration(repo, field, value):
    path = repo / n.MODEL_META
    data = json.loads(path.read_text())
    target = data
    for part in field.split(".")[:-1]:
        target = target[part]
    target[field.split(".")[-1]] = value
    path.write_text(json.dumps(data))
    with pytest.raises(n.NoticeError, match="review and update third_party.yaml"):
        n.check(repo)


def test_binding_cannot_drop_the_model_revision(repo):
    data = registry(repo)
    del data["components"][0]["binds"]["expect"]["recipe.base.revision"]
    save_registry(repo, data)
    with pytest.raises(n.NoticeError, match="metadata bindings"):
        n.check(repo)


@pytest.mark.parametrize("change", ["missing", "unbound", "duplicate"])
def test_wordnet_credit_cannot_disappear_while_metadata_declares_it(repo, change):
    data = registry(repo)
    if change == "missing":
        data["credits"] = []
    elif change == "unbound":
        data["credits"][0]["binds"]["expect"] = {"version": "1.2.0"}
    else:
        data["credits"].append(copy.deepcopy(data["credits"][0]))
    save_registry(repo, data)
    with pytest.raises(n.NoticeError, match="credit bound to the wordnet metadata field"):
        n.validate(repo, freshness=False)


def test_unknown_upstream_licence_is_contextual_before_rendering(repo):
    data = registry(repo)
    data["components"][0]["upstream"][0]["licence"] = "Unlisted"
    save_registry(repo, data)
    with pytest.raises(n.NoticeError, match="licence declarations differ"):
        n.check(repo)


def test_model_upstream_evidence_must_name_the_bound_base(repo):
    data = registry(repo)
    data["components"][0]["upstream"] = data["components"][0]["upstream"][1:]
    save_registry(repo, data)
    with pytest.raises(n.NoticeError, match="upstream evidence must include the bound base"):
        n.check(repo)


@pytest.mark.parametrize("name", ["LICENSE", "LICENSES/MIT.txt"])
@pytest.mark.parametrize("change", ["deleted", "corrupt", "untracked", "symlink"])
def test_licence_evidence_is_required_and_verified(repo, change, name):
    path = repo / name
    if change == "deleted":
        path.unlink()
    elif change == "corrupt":
        path.write_text("Incomplete licence text.")
    elif change == "untracked":
        git(repo, "rm", "--cached", name)
    else:
        path.unlink()
        path.symlink_to(ROOT / name)
    with pytest.raises(n.NoticeError):
        n.check(repo)


def test_stale_notice_diagnostic_has_the_fix_command(repo):
    put(repo, n.NOTICES, "Old notice.\n")
    with pytest.raises(n.NoticeError, match="python scripts/notices.py generate"):
        n.check(repo)


@pytest.mark.parametrize("change", ["header", "cap", "undeclared", "same_remote_name", "missing_declaration"])
def test_remote_excerpts_are_exact_exceptions(repo, change):
    path = "research/retellings-2026-10-11/harnessed/moloch.txt"
    data = yaml.safe_load((repo / "tests/corpus/remote.yaml").read_text())["items"]
    if change == "header":
        put(repo, path, (repo / path).read_text().replace("fair dealing", "other grounds"))
    elif change == "cap":
        put(repo, path, (repo / path).read_text() + " extra" * 300)
    elif change == "undeclared":
        data[0]["excerpts"] = []
    elif change == "missing_declaration":
        del data[1]["excerpts"]
    else:
        put(repo, "somewhere/my_country.txt", "Private work fixture")
        git(repo, "add", "somewhere/my_country.txt")
    put(repo, "tests/corpus/remote.yaml", yaml.safe_dump({"items": data}, sort_keys=False))
    with pytest.raises(n.NoticeError):
        n.check(repo)


@pytest.mark.parametrize("sources", [[], ["https://www.macquariedictionary.com.au/entry/thing"],
                                     ["HTTPS://WWW.OED.COM/entry/thing"], ["not a URL"]])
def test_scraped_sources_must_be_present_and_permitted(repo, sources):
    put(repo, "aussiefy/data/entries/scraped.yaml", yaml.safe_dump([{"id": "fixture", "sources": sources}]))
    with pytest.raises(n.NoticeError, match="source"):
        n.check(repo)


def test_scraped_source_overlays_cannot_bypass_policy(repo):
    put(repo, "aussiefy/data/entries/scraped.yaml", yaml.safe_dump([{"id": "fixture", "sources": ["https://example.com"]}]))
    put(repo, "aussiefy/data/sources.yaml", yaml.safe_dump({"fixture": ["https://oed.com/entry/x"]}))
    with pytest.raises(n.NoticeError, match="reference-only"):
        n.check(repo)


def test_permitted_scraped_source_passes(repo):
    put(repo, "aussiefy/data/entries/scraped.yaml", yaml.safe_dump([{"id": "fixture", "sources": ["https://example.com"]}]))
    n.check(repo)


@pytest.mark.parametrize("policy", [[], {"reference_only": False}, {"reference_only": [{"domain": []}]},
                                   {"reference_only": [{"domain": "example.com", "reason": None}]},
                                   {"reference_only": [{"domain": " ", "reason": "Broken rule"}]}])
def test_malformed_source_policy_is_contextual(repo, policy):
    put(repo, "aussiefy/data/entries/scraped.yaml", yaml.safe_dump([{"id": "fixture", "sources": ["https://example.com"]}]))
    put(repo, "aussiefy/data/source_policy.yaml", yaml.safe_dump(policy))
    with pytest.raises(n.NoticeError, match="source_policy.yaml"):
        n.check(repo)


@pytest.mark.parametrize("change", ["expression", "files", "package_data"])
def test_packaging_cannot_drop_declared_material(repo, change):
    path = repo / "pyproject.toml"
    text = path.read_text()
    if change == "expression":
        text = text.replace('license = "MIT AND Apache-2.0"', 'license = "MIT"')
    elif change == "files":
        text = text.replace('"LICENSES/*.txt", ', "")
    else:
        text = text.replace(', "data/model/*"', "")
    path.write_text(text)
    with pytest.raises(n.NoticeError):
        n.check(repo)


def test_namespaces_setting_must_be_a_boolean(repo):
    path = repo / "pyproject.toml"
    text = path.read_text().replace('include = ["aussiefy*"]', 'include = ["aussiefy*"]\nnamespaces = "false"')
    path.write_text(text)
    with pytest.raises(n.NoticeError, match="namespaces must be a boolean"):
        n.check(repo)


def test_missing_tracked_input_fails_without_a_build(repo):
    (repo / "LICENSE").unlink()
    with pytest.raises(n.NoticeError, match="missing ordinary file"):
        n.check(repo)


@pytest.mark.parametrize("url", ["https://[broken", "http://[:::]"])
def test_malformed_source_url_is_contextual(repo, url):
    put(repo, "aussiefy/data/entries/scraped.yaml", yaml.safe_dump([{"id": "fixture", "sources": [url]}]))
    with pytest.raises(n.NoticeError, match="malformed source URL"):
        n.check(repo)


@pytest.mark.parametrize("value", [None, False, {}, "broken"])
def test_malformed_registry_is_contextual(repo, value):
    put(repo, "third_party.yaml", yaml.safe_dump(value))
    with pytest.raises(n.NoticeError, match="third_party.yaml"):
        n.check(repo)


def make_wheel(repo, target, *, omit=None, corrupt=None, expression=None, extra=None):
    _, project, packaged, licences = n.validate(repo)
    prefix = "aussiefy-0.1.0.dist-info/"
    metadata = Message()
    metadata["Metadata-Version"] = "2.4"
    metadata["License-Expression"] = expression or project["project"]["license"]
    for name in sorted(licences):
        metadata["License-File"] = name
    with ZipFile(target, "w") as archive:
        archive.writestr(prefix + "METADATA", metadata.as_bytes())
        for name in packaged | licences:
            if name == omit:
                continue
            archived = prefix + "licenses/" + name if name in licences else name
            archive.writestr(archived, b"corrupt" if name == corrupt else (repo / name).read_bytes())
        if extra:
            archive.writestr(extra, "undeclared")
    return project, packaged, licences


def test_wheel_inspection_reads_actual_files_and_metadata(repo, tmp_path):
    target = tmp_path / "good.whl"
    values = make_wheel(repo, target)
    n.inspect_wheel(repo, target, *values)


@pytest.mark.parametrize("changes", [
    {"omit": "LICENSES/MIT.txt"}, {"corrupt": "LICENSES/Apache-2.0.txt"}, {"expression": "MIT"},
    {"omit": "aussiefy/data/model/vectors.f16"}, {"extra": "aussiefy/unclaimed.txt"},
    {"extra": "aussiefy-0.1.0.dist-info/licenses/unreviewed.txt"},
])
def test_wheel_inspection_rejects_missing_or_changed_distribution_evidence(repo, tmp_path, changes):
    target = tmp_path / "bad.whl"
    values = make_wheel(repo, target, **changes)
    with pytest.raises(n.NoticeError, match="wheel:"):
        n.inspect_wheel(repo, target, *values)


def test_failed_licence_gate_aborts_promotion_on_the_exact_committed_tree(repo, monkeypatch):
    import promotion

    put(repo, "LICENSES/MIT.txt", "Incomplete fixture licence")
    git(repo, "add", ".")
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Fixture")
    source = git(repo, "rev-parse", "HEAD").strip()
    failures = []

    def run(command, work):
        if "scripts/notices.py" not in command:
            return 0, ""
        assert git(work, "rev-parse", "HEAD").strip() == source
        assert "--wheel" in command
        try:
            n.check(work, wheel=True)
        except n.NoticeError as exc:
            failures.append(str(exc))
            return 2, str(exc)
        return 0, ""

    monkeypatch.setattr(promotion, "run_echoed", run)
    with pytest.raises(promotion.PromotionError, match="nothing was released"):
        promotion.run_checks(promotion.Git(repo), source)
    assert len(failures) == 1 and "reviewed licence text changed" in failures[0]
    assert len(git(repo, "worktree", "list", "--porcelain").split("worktree ")) == 2


def test_cli_generation_is_repeatable_and_check_errors_use_exit_two(repo, monkeypatch, capsys):
    monkeypatch.setattr(n, "__file__", str(repo / "scripts/notices.py"))
    monkeypatch.setattr(sys, "path", sys.path.copy())
    put(repo, n.NOTICES, "Old notice")
    assert n.main(["generate"]) == 0
    first = (repo / n.NOTICES).read_bytes()
    assert n.main(["generate"]) == 0
    assert (repo / n.NOTICES).read_bytes() == first
    put(repo, "LICENSES/MIT.txt", "Broken text")
    assert n.main(["check"]) == 2
    assert "LICENSES/MIT.txt: reviewed licence text changed" in capsys.readouterr().err


def test_cli_checks_from_another_directory():
    result = subprocess.run([sys.executable, str(ROOT / "scripts/notices.py"), "check"], cwd=ROOT.parent,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "checks passed" in result.stdout


@pytest.mark.parametrize("source", ["tests/corpus/unclaimed.txt", "tests/corpus/local/private.txt"])
def test_derived_research_requires_redistributable_declared_source(repo, source):
    put(repo, "research/derived/output.txt", "A derived rewrite.\n")
    put(repo, "research/PROVENANCE.yaml", yaml.safe_dump({"derived": [{
        "source": source, "paths": ["research/derived/*.txt"], "modifications": "Test rewrite."}]}))
    git(repo, "add", "research")
    with pytest.raises(n.NoticeError, match="redistributable corpus claim"):
        n.check(repo)


def test_derived_research_inherits_a_real_source_and_cannot_overlap(repo):
    row = {"source": "tests/corpus/reference/source.txt", "paths": ["research/derived/*.txt"],
           "modifications": "Test rewrite."}
    put(repo, "research/derived/output.txt", "A derived rewrite.\n")
    put(repo, "research/PROVENANCE.yaml", yaml.safe_dump({"derived": [row]}))
    git(repo, "add", "research")
    n.check(repo)
    put(repo, "research/PROVENANCE.yaml", yaml.safe_dump({"derived": [row, row]}))
    with pytest.raises(n.NoticeError, match="duplicate provenance claims"):
        n.check(repo)


def test_derived_research_pattern_must_cover_actual_tracked_work(repo):
    put(repo, "research/PROVENANCE.yaml", yaml.safe_dump({"derived": [{
        "source": "tests/corpus/reference/source.txt", "paths": ["research/missing/**"],
        "modifications": "Test rewrite."}]}))
    with pytest.raises(n.NoticeError, match="no tracked files"):
        n.check(repo)


@pytest.mark.parametrize("path", ["aussiefy/data/pos/tagger.json.gz", "research/licences/LGPL-3.0.txt"])
def test_new_third_party_digest_bindings_reject_modified_bytes(repo, path):
    target = repo / path
    target.write_bytes(target.read_bytes() + b"changed")
    with pytest.raises(n.NoticeError, match="digest"):
        n.check(repo)
