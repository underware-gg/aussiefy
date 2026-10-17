"""Contextual imagery: reviewed meanings, usage constraints and grammatical suggestions."""

from __future__ import annotations

from dataclasses import dataclass

from .realise import noun_slots
from .schema import Imagery, PLACEHOLDER_RE
from .select import form_problem, person_subject
from .terms import form_key
from .text import tokenize


@dataclass(frozen=True)
class ImageOffer:
    image: Imagery
    text: str
    association: str

    @property
    def tone(self):
        return self.image.tone

    def card(self):
        i = self.image
        return {"id": i.id, "text": self.text, "tone": i.tone, "form": i.form, "concepts": list(i.concepts),
                "association": self.association, "subject": i.subject, "exaggeration": i.exaggeration,
                "frames": list(i.frames),
                "unless_after": list(i.unless_after),
                "origin": i.origin, "usage": i.usage,
                "automatic": i.form == "suffix" and self.association == "direct"}


def image_association(image, concepts, setting):
    if set(image.concepts) & set(concepts):
        return "direct"
    if setting.riff_association and set(image.related) & set(concepts):
        return "related"
    return None


def permitted(image, level, cap, setting):
    return (setting.takes("riff") and setting.contextual_riffs and image.level <= level
            and image.vulgarity <= cap and image.exaggeration <= setting.riff_exaggeration)


def positive_context(det, tokens):
    start = det.start
    while start > 0 and tokens[start - 1].text not in {".", "!", "?", ";", ":"} and tokens[start - 1].norm not in {"and", "but", "or"}:
        start -= 1
    return not any(t.norm in {"not", "n't", "never", "no", "without"} for t in tokens[start:det.end])


def excluded_complement(image, tokens, end):
    following = next((t.norm for t in tokens[end:] if not t.is_punct), None)
    return following in image.unless_after


def image_offers(dictionary, det, tokens, level, cap, setting):
    if not setting.contextual_riffs or not setting.takes("riff") or not positive_context(det, tokens):
        return ()
    out = []
    for image in dictionary.imagery:
        association = image_association(image, det.concepts, setting)
        if not association or not permitted(image, level, cap, setting) or det.frame not in image.frames:
            continue
        if excluded_complement(image, tokens, det.end):
            continue
        if image.subject == "person" and not person_subject(det, dictionary.person_nouns):
            continue
        if form_problem(image.text, det) or ("{poss}" in image.text and not {"poss", "subj", "agent"} & det.captures.keys()):
            continue
        values = noun_slots(det)
        bound = PLACEHOLDER_RE.sub(lambda m: values[m.group(1)], image.text)
        out.append(ImageOffer(image, bound, association))
    return tuple(out)


def lookup_images(dictionary, query, level, cap, setting, limit):
    tokens = tokenize(query)
    matches = list(dictionary.index.find(tokens))
    positive = not any(t.norm in {"not", "n't", "never", "no", "without"} for t in tokens)
    key = form_key(query)
    out = []
    for image in dictionary.imagery:
        if not permitted(image, level, cap, setting):
            continue
        concepts = {cid for m in matches if not excluded_complement(image, tokens, m.end) for cid in m.pattern.concepts}
        association = image_association(image, concepts, setting) if positive else None
        words = form_key(image.text)
        literal = key == words or (len(key) >= 4 and f" {key} " in f" {words} ") or key == form_key(image.id.replace("-", " "))
        if not association and not literal:
            continue
        card = ImageOffer(image, image.text, association or "image search").card()
        card.update(template=True, automatic=False)
        out.append(card)
    return out[:limit]
