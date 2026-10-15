"""The staging files the scrape pipeline passes between steps, and the ids it gives new phrases."""

import pytest

from aussiefy.errors import UserError
from aussiefy.scrape.normalise import Staged, load_staged, save_staged, unique_id


def test_unique_id_numbers_past_taken_ids_and_takes_its_own():
    taken = {"fair-dinkum", "fair-dinkum-2"}
    assert unique_id("Fair dinkum!", taken) == "fair-dinkum-3" and "fair-dinkum-3" in taken
    assert unique_id("Fair dinkum", taken) == "fair-dinkum-4"
    assert unique_id("Arvo", taken) == "arvo"


def test_staging_round_trips(tmp_path):
    items = [Staged("arvo", "arvo", sources=["https://example.com"], usage=["See ya this arvo."]),
             Staged("goog", "goog", known_as="full-as-a-goog", known_status="active")]
    path = tmp_path / "deep" / "s.yaml"
    save_staged(path, items)
    assert load_staged(path) == items


@pytest.mark.parametrize("content, message", [("[unclosed", "invalid YAML"), ("{a: 1}", "not a staging file"),
                                              ("- {form: x}", r"phrase 1 needs an id and a form, got \{'form': 'x'\}"),
                                              ("false", "not a staging file"), ("0", "not a staging file"),
                                              ("{}", "not a staging file"),
                                              ("- {id: x, form: null}", "phrase 1: form"),
                                              ("- {id: x, form: x, sources: null}", "phrase 1: sources"),
                                              ("- {id: x, form: x, variants: [3]}", "phrase 1: variants")])
def test_a_bad_staging_file_is_a_user_error(tmp_path, content, message):
    path = tmp_path / "s.yaml"
    path.write_text(content)
    with pytest.raises(UserError, match=message):
        load_staged(path)
    with pytest.raises(UserError, match="no such staging file"):
        load_staged(tmp_path / "missing.yaml")


def test_an_empty_staging_document_is_supported(tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_text("")
    assert load_staged(path) == []

