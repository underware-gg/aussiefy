"""Aim preferences refine resolved permissions; cap keeps the historical policy."""
from dataclasses import dataclass, replace
import math

from .errors import SchemaError, UserError
from .model import SwearProfile
from .profile import ProfileOverrides


@dataclass(frozen=True)
class DialGoals:
    tier_decay: float
    swearing: dict[int, SwearProfile]
    embellishment: dict[int, ProfileOverrides]


def parse_goals(raw):
    if not raw:
        return None
    if not isinstance(raw, dict) or set(raw) != {'tier_decay', 'swearing', 'embellishment'}:
        raise SchemaError('dial-goals.yaml needs tier_decay, swearing and embellishment')
    decay = raw['tier_decay']
    if type(decay) not in (int, float) or not math.isfinite(decay) or not 0 < decay <= 1:
        raise SchemaError('dial-goals.yaml tier_decay must be greater than zero and at most one')
    if not isinstance(raw['swearing'], dict) or set(raw['swearing']) != set(range(4)):
        raise SchemaError('dial-goals.yaml swearing needs stops 0–3')
    if not isinstance(raw['embellishment'], dict) or set(raw['embellishment']) != set(range(3)):
        raise SchemaError('dial-goals.yaml embellishment needs stops 0–2')
    try:
        swearing = {k: replace(SwearProfile(), **ProfileOverrides.parse({'swearing': v}).values()['swearing'])
                    for k, v in raw['swearing'].items()}
        profiles = {k: ProfileOverrides.parse(v) for k, v in raw['embellishment'].items()}
    except UserError as exc:
        raise SchemaError(f'dial-goals.yaml: {exc}') from exc
    # Level controls word substitution, frames and drawl in either mode.
    allowed = {'garnish', 'max_garnish', 'garnish_gap', 'garnish_per_sentence'}
    if any(set(p.values()) - allowed for p in profiles.values()):
        raise SchemaError('dial-goals.yaml embellishment may tune only garnish rates, budgets and spacing')
    return DialGoals(float(decay), swearing, profiles)


def resolve_goals(effective, policy, dictionary, setting):
    if policy.dial_mode != 'aim' or dictionary.dial_goals is None:
        return effective
    goals = dictionary.dial_goals
    profile, swearing = goals.embellishment[setting.step].apply(
        effective.profile, goals.swearing[effective.vulgarity])
    # Explicit profile values are authoritative, including zero and empty maps.
    if policy.document_config.profile is not None:
        profile, swearing = policy.document_config.profile.apply(profile, swearing)
    explicit = policy.document_config.profile.values().get('garnish', {}) if policy.document_config.profile else {}
    rates = dict(profile.garnish)
    for placement in ('opener', 'tag', 'aside', 'tail', 'closer'):
        if placement not in explicit:
            swear = swearing.closer if placement == 'closer' else swearing.exclaim
            rates[placement] = 1 - (1 - rates.get(placement, 0)) * (1 - swear)
    profile = replace(profile, garnish=rates)
    return replace(effective, profile=profile, swearing=swearing, tier_decay=goals.tier_decay)
