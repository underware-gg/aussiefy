"""Contextual imagery: reviewed meanings, usage constraints and grammatical suggestions."""

from __future__ import annotations

from dataclasses import dataclass

from .realise import noun_slots
from .schema import Imagery, PLACEHOLDER_RE
from .select import binding_problem
from .context import following_context, positive_context
from .detect import person_subject
from .terms import form_key
from .cards import metadata
from .evidence import metadata_rejections, theme_rejection, register_rejection


@dataclass(frozen=True)
class ImageOffer:
    image: Imagery
    text: str
    association: str

    @property
    def tone(self):
        return self.image.tone

    def card(self, permitted_themes):
        i = self.image
        return {"id": i.id, "text": self.text, "tone": i.tone, "form": i.form, "concepts": list(i.concepts),
                "association": self.association, "subject": i.subject, "exaggeration": i.exaggeration,
                "frames": list(i.frames),
                "unless_after": list(i.unless_after),
                **metadata(i, permitted_themes), "usage": i.usage,
                "automatic": i.form == "suffix" and self.association == "direct"}


def image_association(image, concepts, setting):
    if set(image.concepts) & set(concepts):
        return "direct"
    if setting.riff_association and set(image.related) & set(concepts):
        return "related"
    return None


def permitted(image, eff, setting):
    return (setting.takes("riff") and setting.contextual_riffs and image.level <= eff.level
            and image.vulgarity <= eff.vulgarity and image.exaggeration <= setting.riff_exaggeration
            and not metadata_rejections(image, allow_misreadable=eff.allow_misreadable) and not theme_rejection(image, eff.theme_policy)
            and not register_rejection(image, eff.registers))


def excluded_complement(image, tokens, end):
    following = following_context(tokens, end)
    return bool(image.unless_after) and (not following.known or following.word in image.unless_after)


def image_offers(dictionary, det, tokens, eff, setting):
    if not setting.contextual_riffs or not setting.takes("riff") or not positive_context(tokens, det.start, det.end):
        return ()
    out = []
    for image in dictionary.imagery:
        association = image_association(image, det.concepts, setting)
        if not association or not permitted(image, eff, setting) or det.frame not in image.frames:
            continue
        if excluded_complement(image, tokens, det.end):
            continue
        if image.subject == "person" and not person_subject(det, dictionary.person_nouns):
            continue
        if binding_problem(image.text, det) or ("{poss}" in image.text and not {"poss", "subj", "agent"} & det.captures.keys()):
            continue
        values = noun_slots(det)
        bound = PLACEHOLDER_RE.sub(lambda m: values[m.group(1)], image.text)
        out.append(ImageOffer(image, bound, association))
    return tuple(out)


def lookup_images(dictionary, query, eff, setting, limit, *, tokens, readings) -> tuple[list[dict], bool]:
    """Eligible image cards and whether the query recognised any image before policy gates."""
    key = form_key(query)
    out, recognised = [], False
    for image in dictionary.imagery:
        concepts = {cid for reading in readings if not excluded_complement(image, tokens, reading.end)
                    and positive_context(tokens, reading.start, reading.end) for cid in reading.concepts}
        association = image_association(image, concepts, setting)
        words = form_key(image.text)
        exact = key in {words, form_key(image.id.replace('-', ' '))}
        literal = exact or (len(key) >= 4 and f" {key} " in f" {words} ")
        if not association and not literal:
            continue
        recognised = True
        if not permitted(image, eff, setting):
            continue
        card = ImageOffer(image, image.text, association or "image search").card(eff.theme_policy)
        card.update(template=True, automatic=False,
                    match_kind='meaning' if association else 'term' if exact else 'phrase')
        out.append(card)
    return out[:limit], recognised
