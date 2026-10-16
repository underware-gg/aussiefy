"""The judge: blind packets, rubric-shaped reports validated and unblinded, verdicts tallied; the model faked."""

import json
from types import SimpleNamespace

import pytest

from aussiefy import judge as j

ORIGINAL = "The boy cried wolf. Nobody came. The wolf ate the sheep."
CANDIDATES = {"engine": "The young fella cried wolf. Nobody came. The wolf scoffed the jumbucks.",
              "yarn": "So the kid sings out wolf, yeah? Not a soul turns up. Wolf has the sheep for tea.",
              "unharnessed": "Little bloke yells wolf. No-one shows. Wolf gets stuck into the sheep."}


@pytest.fixture
def packet(translator):
    return j.blind(ORIGINAL, CANDIDATES, level=4, seed=3, translator=translator)


def report_for(packet, rubric, *, best="A", score=4, quote=None):
    labels = list(packet.candidates)
    order = [[best]] + [[lb] for lb in labels if lb != best]
    return {"candidates": {lb: {
        "scores": {c.id: {"evidence": f"saw {c.id}", "score": score} for c in rubric.criteria},
        "problems": [{"quote": quote or packet.candidates[lb].split(".")[0], "original": "The boy cried wolf",
                      "severity": "minor", "why": "could be stronger"}],
        "summary": f"candidate {lb}"} for lb in labels},
        "rankings": {k: order for k in rubric.compared}}


def test_blind_is_deterministic_and_hides_the_names(packet, translator):
    assert packet == j.blind(ORIGINAL, CANDIDATES, level=4, seed=3, translator=translator)
    orders = {tuple(j.blind(ORIGINAL, CANDIDATES, seed=s, translator=translator).names.values()) for s in range(12)}
    assert len(orders) > 1                                       # the seed changes the order
    prompt = packet.prompt()
    assert all(f"CANDIDATE {name}:" not in prompt for name in CANDIDATES)
    assert sorted(packet.names.values()) == sorted(CANDIDATES) and list(packet.candidates) == ["A", "B", "C"]


def test_the_schema_asks_for_evidence_before_the_score(packet):
    rubric = j.Rubric.load()
    schema = packet.schema(rubric)
    cand = schema["properties"]["candidates"]["properties"]["A"]
    assert set(cand["properties"]["scores"]["required"]) == {c.id for c in rubric.criteria}
    assert list(cand["properties"]["scores"]["properties"]["meaning"]["properties"]) == ["evidence", "score"]
    assert set(schema["properties"]["rankings"]["required"]) == {"tone", "flow", "variety", "essence", "overall"}


def test_a_good_report_unblinds(packet):
    rubric = j.Rubric.load()
    v = j.read(packet, report_for(packet, rubric, best="B"), rubric, judge="test")
    assert set(v.scores) == set(CANDIDATES) and v.rankings["overall"][0] == [packet.names["B"]]
    assert v.labels[packet.names["B"]] == "B" and "mean" in v.card()


def test_a_bad_report_lists_every_problem(packet):
    rubric = j.Rubric.load()
    bad = report_for(packet, rubric, quote="a line nobody wrote")
    bad["candidates"]["A"]["scores"]["meaning"]["score"] = 7
    bad["candidates"]["B"]["scores"]["flow"]["evidence"] = ""
    bad["rankings"]["overall"] = [["A"], ["A", "B"]]
    del bad["candidates"]["C"]
    with pytest.raises(j.BadReport) as exc:
        j.read(packet, bad, rubric)
    text = " ".join(exc.value.problems)
    for want in ("A meaning: score", "B flow: evidence", "isn't in candidate", "ranking 'overall'", "C not reported"):
        assert want in text, want


def test_ties_share_a_tier_and_first_place(packet):
    rubric = j.Rubric.load()
    tied = report_for(packet, rubric)
    tied["rankings"] = {k: [["A", "C"], ["B"]] for k in rubric.compared}
    tied["candidates"]["A"]["problems"][0]["original"] = ""          # an added line renders nothing
    v = j.read(packet, tied, rubric)
    assert v.rankings["overall"] == [[packet.names["A"], packet.names["C"]], [packet.names["B"]]]
    assert j.tally([v])[packet.names["A"]]["first"] == 0.5 and "(added)" in v.card()


def test_tally_averages_across_texts(packet):
    rubric = j.Rubric.load()
    v1 = j.read(packet, report_for(packet, rubric, best="A", score=4), rubric)
    v2 = j.read(packet, report_for(packet, rubric, best="A", score=2), rubric)
    t = j.tally([v1, v2])
    first = packet.names["A"]
    assert t[first]["first"] == 1.0 and t[first]["mean"] == 3.0 and t[first]["texts"] == 2
    assert t[first]["problems"]["minor"] == 2


def _reply(obj):
    return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(obj))])


def test_run_sends_a_bad_report_back_once_then_caches(packet, tmp_path):
    rubric = j.Rubric.load()
    bad = report_for(packet, rubric, quote="a line nobody wrote")
    good = report_for(packet, rubric, best="C")
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return _reply(bad if len(calls) == 1 else good)

    client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    v = j.run(packet, client=client, model="m", cache_dir=str(tmp_path))
    assert v.rankings["overall"][0] == [packet.names["C"]] and len(calls) == 2
    assert "doesn't follow the rubric" in calls[1]["messages"][-1]["content"]
    assert calls[0]["output_config"]["format"]["schema"] == packet.schema(rubric)
    assert j.run(packet, client=None, model="m", cache_dir=str(tmp_path)).scores == v.scores   # cached


def test_the_unharnessed_brief_carries_the_dials():
    prompt = j.unharnessed_prompt(ORIGINAL, level=2, vulgarity=0)
    assert "lightly Aussie" in prompt and "no swearing" in prompt and ORIGINAL in prompt


def test_cli_brief_then_read(tmp_path, capsys, packet):
    from aussiefy.cli import main

    (tmp_path / "o.txt").write_text(ORIGINAL)
    args = []
    for name, text in CANDIDATES.items():
        (tmp_path / f"{name}.txt").write_text(text)
        args += ["--candidate", f"{name}={tmp_path / name}.txt"]
    out = tmp_path / "packet.json"
    assert main(["judge", "brief", str(tmp_path / "o.txt"), *args, "-l", "4", "-s", "3", "-o", str(out)]) == 0
    seen = json.loads(capsys.readouterr().out)
    assert set(seen) == {"instructions", "prompt", "schema"}       # the judge never sees the key
    saved = j.Packet.from_dict(json.loads(out.read_text()))
    assert saved == packet
    (tmp_path / "report.json").write_text(json.dumps(report_for(saved, j.Rubric.load(), best="A")))
    assert main(["judge", "read", str(out), str(tmp_path / "report.json")]) == 0
    assert "rankings:" in capsys.readouterr().out
    (tmp_path / "bad.json").write_text("{}")
    assert main(["judge", "read", str(out), str(tmp_path / "bad.json")]) == 1


def test_the_shipped_rubric_is_well_formed():
    rubric = j.Rubric.load()
    ids = [c.id for c in rubric.criteria]
    assert len(ids) == len(set(ids)) and "overall" not in ids
    assert all(set(c.anchors) == {1, 3, 5} and c.question.endswith("?") for c in rubric.criteria)
    assert "evidence first" in rubric.text()


def test_the_unharnessed_brief_carries_yarn_modes_markup_rule():
    doc = "# Title\n\nRun `make` when you are very tired. See [docs](https://x.y).\n"
    prompt = j.unharnessed_prompt(doc, level=3, vulgarity=1, markup="auto")
    assert "markdown document" in prompt and "character for character" in prompt
    assert "character for character" not in j.unharnessed_prompt("Plain words.", level=3, vulgarity=1)


def test_a_misshapen_report_is_sent_back_not_crashed_on(packet):
    """A hand-written report (`aussiefy judge read`) can be any JSON: every bad shape comes back as BadReport."""
    rubric = j.Rubric.load()
    good = report_for(packet, rubric)
    shapes = [[], {"candidates": "A"}, {**good, "candidates": {**good["candidates"], "A": "oops"}},
              {**good, "candidates": {lb: {**c, "problems": ["too formal"]} for lb, c in good["candidates"].items()}},
              {**good, "candidates": {lb: {**c, "problems": [{"quote": 5}]} for lb, c in good["candidates"].items()}}]
    for bad in shapes:
        with pytest.raises(j.BadReport):
            j.read(packet, bad, rubric)


@pytest.mark.parametrize('broken', ['rankings_string', 'ranking_nonstring', 'score_bool', 'evidence_null', 'summary_null', 'problems_missing'])
def test_malformed_reports_are_bad_reports_not_programming_errors(packet, broken):
    rubric = j.Rubric.load()
    report = report_for(packet, rubric)
    label = next(iter(packet.candidates))
    criterion = rubric.criteria[0].id
    if broken == 'rankings_string':
        report['rankings'] = 'oops'
    elif broken == 'ranking_nonstring':
        report['rankings'][rubric.compared[0]] = [[label], [1]]
    elif broken == 'score_bool':
        report['candidates'][label]['scores'][criterion]['score'] = True
    elif broken == 'evidence_null':
        report['candidates'][label]['scores'][criterion]['evidence'] = None
    elif broken == 'summary_null':
        report['candidates'][label]['summary'] = None
    else:
        del report['candidates'][label]['problems']
    with pytest.raises(j.BadReport):
        j.read(packet, report, rubric)


@pytest.mark.parametrize("changed,value", [
    ("original", 7), ("level", True), ("vulgarity", 4), ("rubric_version", None),
    ("candidates", []), ("candidates", {"AA": "first", "B": "second"}),
    ("key", {}), ("key", {"A": "same", "B": "same", "C": "same"}),
])
def test_packet_deserialisation_rejects_wrong_shapes(packet, changed, value):
    from aussiefy.errors import UserError

    data = packet.to_dict(j.Rubric.load())
    data[changed] = value
    with pytest.raises(UserError, match="fixture-packet"):
        j.Packet.from_dict(data, where="fixture-packet")


@pytest.mark.parametrize("changed,value", [
    ("rubric_version", True), ("scores", []), ("scores", {"a": {"meaning": True}, "b": {"meaning": 3}}),
    ("evidence", {}), ("problems", []), ("summaries", {}), ("rankings", {}),
    ("rankings", {"overall": [[1]]}), ("rankings", {"overall": [["engine", "engine", "yarn"]]}),
    ("judge", None), ("labels", {"engine": "AA"}),
])
def test_verdict_deserialisation_rejects_wrong_shapes(packet, changed, value):
    from aussiefy.errors import UserError

    rubric = j.Rubric.load()
    data = j.read(packet, report_for(packet, rubric), rubric).to_dict()
    data[changed] = value
    with pytest.raises(UserError, match="fixture-verdict"):
        j.Verdict.from_dict(data, where="fixture-verdict")


def test_serialised_verdict_round_trips_and_tallies(packet):
    rubric = j.Rubric.load()
    verdict = j.read(packet, report_for(packet, rubric), rubric)
    restored = j.Verdict.from_dict(json.loads(json.dumps(verdict.to_dict())))
    assert restored == verdict and j.tally([restored]) == j.tally([verdict])


@pytest.mark.parametrize("kind,content", [("packet", "{}"), ("packet", "{invalid"),
                                         ("report", "{invalid"), ("verdict", "[]")])
def test_cli_judge_json_errors_name_the_input(tmp_path, capsys, packet, kind, content):
    from aussiefy.cli import main

    bad = tmp_path / "bad.json"
    bad.write_text(content)
    good = tmp_path / "packet.json"
    good.write_text(json.dumps(packet.to_dict(j.Rubric.load())))
    args = ["judge", "tally", str(bad)] if kind == "verdict" else [
        "judge", "read", str(bad) if kind == "packet" else str(good), str(bad)]
    assert main(args) == 2
    assert str(bad) in capsys.readouterr().err


def test_tally_rejects_incomparable_criteria(packet):
    from aussiefy.errors import UserError

    rubric = j.Rubric.load()
    verdict = j.read(packet, report_for(packet, rubric), rubric)
    data = verdict.to_dict()
    data["scores"] = {name: {"different": 3} for name in verdict.scores}
    data["evidence"] = {name: {"different": "Evidence."} for name in verdict.scores}
    data["rankings"] = {"overall": data["rankings"]["overall"]}
    other = j.Verdict.from_dict(data)
    with pytest.raises(UserError, match="different criteria"):
        j.tally([verdict, other])


@pytest.mark.parametrize("document_type", ["general", "custom", "auto", "technical", "news", "official", "instructions"])
def test_judge_contract_matches_effective_writer_settings(translator, document_type):
    from aussiefy.retelling import brief

    source = '# Settings\n\nRun `worker --check` when you are very tired. “Keep this wording.”\n'
    settings = {"level": "swaggie", "vulgarity": "dad", "embellishment": "dinkum", "markup": "auto",
                "english": "uk", "document_type": document_type,
                "document_config": {"garnish": [], "keep_quotes": True, "person_swears": False,
                                    "profile": {"phonetic": 0.25, "stack": 0, "garnish_gap": 3}}}
    writer = brief(source, translator=translator, **settings)
    packet = j.blind(source, {"producer-canary-one": source, "producer-canary-two": source},
                     translator=translator, **settings)
    contract = packet.evaluation_contract
    assert packet.evaluation_protocol == 2
    assert (contract["level"], contract["vulgarity"]) == (writer.level, writer.vulgarity)
    for key in ("document_config", "profile_config", "embellishment", "genre"):
        assert contract[key] == writer.payload[key.upper()]
    assert contract["markup"] == writer.markup == "markdown"
    assert contract["markup_rules"] == writer.payload["MARKUP"]
    assert contract["english"] == "uk"
    assert "producer-canary" not in json.dumps(packet.judging(j.Rubric.load()))
    assert j.Packet.from_dict(json.loads(json.dumps(packet.to_dict(j.Rubric.load())))) == packet


@pytest.mark.parametrize("field", ["substitution", "garnish", "max_garnish", "rewrite", "swearing"])
def test_saved_judge_contract_requires_every_nested_profile_setting(packet, field):
    data = packet.to_dict(j.Rubric.load())
    # Roundtrip first so the intentionally edited external JSON cannot mutate the in-memory packet.
    data = json.loads(json.dumps(data))
    settings = data["evaluation_contract"]["profile_config"][field]
    del settings[next(iter(settings))]
    with pytest.raises(j.UserError, match="fixture.*complete nested"):
        j.Packet.from_dict(data, where="fixture")


@pytest.mark.parametrize("field,value", [
    ("evaluation_protocol", True), ("evaluation_protocol", 3), ("evaluation_contract", None),
    ("evaluation_contract", {}),
])
def test_saved_judge_contract_rejects_invalid_protocol_or_missing_snapshot(packet, field, value):
    data = json.loads(json.dumps(packet.to_dict(j.Rubric.load())))
    data[field] = value
    with pytest.raises(j.UserError, match="fixture"):
        j.Packet.from_dict(data, where="fixture")


@pytest.mark.parametrize("change", ["level", "markup", "document", "profile", "numeric"])
def test_saved_judge_contract_rejects_invalid_effective_settings(packet, change):
    data = json.loads(json.dumps(packet.to_dict(j.Rubric.load())))
    contract = data["evaluation_contract"]
    if change == "level":
        contract["level"] = 1 if data["level"] != 1 else 2
    elif change == "markup":
        contract["markup"] = "auto"
    elif change == "document":
        del contract["document_config"]["keep_quotes"]
    elif change == "profile":
        del contract["profile_config"]["phonetic"]
    else:
        contract["profile_config"]["garnish"]["tag"] = -0.1
    with pytest.raises(j.UserError, match="fixture"):
        j.Packet.from_dict(data, where="fixture")


def test_legacy_packet_and_verdict_keep_their_original_protocol(packet):
    rubric = j.Rubric.load()
    legacy = j.Packet(packet.original, packet.level, packet.vulgarity, packet.candidates, packet.names,
                      packet.rubric_version)
    saved = legacy.to_dict(rubric)
    assert not {"evaluation_protocol", "evaluation_contract"} & saved.keys()
    restored = j.Packet.from_dict(json.loads(json.dumps(saved)))
    assert restored == legacy and restored.evaluation_protocol == 1
    assert restored.instructions(rubric) == rubric.text() and "EVALUATION_CONTRACT" not in restored.prompt()
    report = report_for(packet, rubric)
    old = j.read(restored, report, rubric)
    current = j.read(packet, report, rubric)
    assert old.evaluation_protocol == 1 and "evaluation_protocol" not in old.to_dict()
    assert j.Verdict.from_dict(old.to_dict()) == old
    assert current.evaluation_protocol == current.to_dict()["evaluation_protocol"] == 2
    assert j.Verdict.from_dict(current.to_dict()) == current
    with pytest.raises(j.UserError, match="different evaluation protocols"):
        j.tally([old, current])


def test_api_judge_uses_agent_instructions_and_contract_sensitive_cache(packet, tmp_path, monkeypatch, translator):
    from conftest import FakeClaude

    rubric = j.Rubric.load()
    changed = j.blind(ORIGINAL, CANDIDATES, level=4, seed=3, translator=translator,
                      document_config={"profile": {"phonetic": 0}})
    good = report_for(packet, rubric)
    client = FakeClaude(_reply(good), _reply(good), _reply(good))
    for item in (packet, changed):
        j.run(item, client=client, model="offline", cache_dir=tmp_path)
        sent = client.kwargs
        assert sent["system"] == item.judging(rubric)["instructions"]
        assert sent["messages"][0]["content"] == item.judging(rubric)["prompt"]
    assert len(client.calls) == 2
    j.run(packet, client=FakeClaude(), model="offline", cache_dir=tmp_path)
    monkeypatch.setattr(j, "CONTRACT_INSTRUCTIONS", j.CONTRACT_INSTRUCTIONS + "\nRevised judge guidance.")
    j.run(packet, client=client, model="offline", cache_dir=tmp_path)
    assert len(client.calls) == 3 and len(list(tmp_path.glob("*.json"))) == 3


def test_reference_writer_receives_contract_without_judge_scoring_directions(translator):
    from conftest import FakeClaude, reply, text_block

    source = "# Settings\n\nRun `worker --check`.\n"
    settings = {"level": 5, "vulgarity": 0, "embellishment": "deadset", "markup": "auto",
                "document_type": "custom", "document_config": {"keep_quotes": True,
                      "profile": {"phonetic": 0, "garnish": {"tag": 0}}}, "translator": translator}
    prompt = j.unharnessed_prompt(source, **settings)
    assert "EVALUATION_CONTRACT" in prompt and '"phonetic": 0' in prompt
    assert "every anonymous candidate" not in prompt and "eight rubric criteria" not in prompt
    client = FakeClaude(reply(text_block(source)))
    assert j.unharnessed(source, client=client, **settings) == source.strip()
    assert client.kwargs["messages"][0]["content"] == prompt


def test_cli_judge_routes_carry_advanced_writing_settings(tmp_path, capsys, monkeypatch):
    from aussiefy.cli import main

    source = "# Settings\n\nRun `worker --check` when you are very tired.\n"
    original = tmp_path / "source.md"
    original.write_text(source)
    first, second = tmp_path / "first.md", tmp_path / "second.md"
    first.write_text(source)
    second.write_text(source)
    config = {"keep_quotes": True, "garnish": [], "profile": {"phonetic": 0.2, "stack": 0}}
    flags = ["--markup", "auto", "--english", "uk", "--document-type", "custom", "-l", "4",
             "--vulgarity", "0", "-e", "dinkum", "--document-config", json.dumps(config)]
    saved = tmp_path / "packet.json"
    candidates = [str(original), "--candidate", f"first={first}", "--candidate", f"second={second}"]
    assert main(["judge", "brief", *candidates, *flags, "-o", str(saved)]) == 0
    visible = json.loads(capsys.readouterr().out)
    packet = j.Packet.from_dict(json.loads(saved.read_text()))
    assert visible == packet.judging(j.Rubric.load())
    assert packet.evaluation_contract["document_type"] == "custom"
    assert packet.evaluation_contract["profile_config"]["phonetic"] == 0.2
    assert packet.evaluation_contract["markup"] == "markdown"
    calls = []

    def run(item, **kwargs):
        calls.append(item)
        return j.read(item, report_for(item, j.Rubric.load()))

    def reference(text, **kwargs):
        assert text == source and kwargs["document_config"] == config
        assert kwargs["markup"] == "auto" and kwargs["english"] == "uk"
        return source

    monkeypatch.setattr(j, "run", run)
    monkeypatch.setattr(j, "unharnessed", reference)
    assert main(["judge", "run", *candidates, *flags, "--json"]) == 0
    capsys.readouterr()
    assert calls[-1].evaluation_contract == packet.evaluation_contract
    assert main(["judge", "run", str(original), "--candidate", f"first={first}", "--unharnessed", *flags,
                 "--json"]) == 0
    capsys.readouterr()
    assert calls[-1].evaluation_contract == packet.evaluation_contract
    assert main(["judge", "unharnessed", str(original), *flags, "--prompt-only"]) == 0
    prompt = capsys.readouterr().out
    assert '"phonetic": 0.2' in prompt and '"keep_quotes": true' in prompt
    assert main(["judge", "unharnessed", str(original), *flags]) == 0
    assert capsys.readouterr().out.strip() == source.strip()
