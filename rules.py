# import libraries and classes
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

# Import DieFace to safely inspect valid fields
from dice_model import DieFace


class Window(Enum):
    """Specifies the timing *Window* per MCP core rules when a
    modification is made.
    """
    BEFORE_RESOLVE_CRITS = "before_resolve_crits"
    ATTACKER_MOD_SELF = "attacker_mod_self"
    DEFENDER_MOD_SELF = "defender_mod_self"
    ATTACKER_MOD_DEFENDER = "attacker_mod_defender"
    DEFENDER_MOD_ATTACKER = "defender_mod_attacker"
    BEFORE_CALC_SUCCESS = "before_calc_success"


@dataclass(frozen=True)
class FaceAlias:
    """Makes a die count as a different face for all game-rule
    purposes (values, modifiability, explode-eligibility, and any
    other rule that matches against a face name) without physically
    changing what's recorded as the die's actual rolled face.

    Distinct from an ActiveRule whose effect changes a face outright
    (e.g. Grand Illusion) — that's a real, physical change; this is
    a standing "for game purposes, treat it as" substitution.
    """

    face: str
    """The physical face this alias applies to (e.g. "Skull")."""

    treated_as: str
    """The face it's treated as for every game-rule purpose (e.g.
    "Critical").
    """


@dataclass(frozen=True, kw_only=True)
class DiceModQuantity:
    """Computes how many dice a rule's effect is scaled to, based on
    a source roll's face counts.

    This is the rule's own formula result only — it does not account
    for how many dice are modifiable; that clamp happens separately
    when the rule is applied.
    """

    max_quantity: int | None
    """The upper limit imposed by this field alone, before the
    formula's own scaling is considered.

    None = no additional ceiling beyond what the formula computes
    (e.g., Warrior of Legend, whose limit is fully determined by
    coefficient * count of faces_to_count), or no formula at all,
    meaning every target-matching die (e.g., Reroll All).
    1 = fixed or gated limits.
    """

    coefficient: int = 1
    """Multiplier applied to faces_to_count (e.g. 2 = 2 uses per
    source face); unused when faces_to_count is None.
    """

    faces_to_count: Sequence[str] | None = None
    """None = doesn't depend on specific faces
    """

    matching_rule: Literal["any", "all"] = "any"
    """ "any" = counts sum independently (Warrior of Legend);
    "all" = every listed face must be present at least once,
    or this contributes nothing (Crossbones)
    """

    source_roll: Literal["own", "opponent"] | None = None
    """"own" or "opponent" — which roll to count faces_to_count in
    """


@dataclass(frozen=True, kw_only=True)
class PropertyOverride:
    """Overrides a single per-die property (e.g. its success value, or
    whether it's modifiable) to a new value for one specific face.

    This class carries no notion of *when* or *how long* the override
    applies — that's determined entirely by where an instance is used:
    inside a PassiveRule, it's persistent for the whole attack; inside an
    ActiveRule's temporary_overrides, it applies only while that specific
    rule is being executed, then reverts.
    """

    face: str
    """The face this override applies to (e.g. "Skull", "Wild").
    """

    property: str | Sequence[str]
    """Name of the DieFace attribute being overridden — e.g.
    "attack_value", "is_modifiable". Must match a
    real field name on DieFace; a typo here will raise an AttributeError.
    """

    effect: int | bool
    """The new value this face's property becomes while the override is
    in effect.
    """

    applies_to_roll: Literal["own", "opponent"] = "own"
    """"own" (default) or "opponent" — which side's roll this override
    applies to. Defaults to "own" since most overrides describe a
    character's own dice; Grand Illusion's opponent-explode
    restriction is the case that needs "opponent" explicitly."""

    def __post_init__(self) -> None:
        """Validates that the target property explicitly exists
        on the DiceFace model."""
        properties = [self.property] if isinstance(self.property, str) \
            else self.property
        for prop in properties:
            if not hasattr(DieFace, prop):
                raise AttributeError(
                    f"PropertyOverride target invalid attribute '{prop}'. "
                    f"Must match a valid field on DieFace."
                )


@dataclass(frozen=True, kw_only=True)
class ActiveRule:
    """A rule a player may optionally choose to invoke during a specific
    modification window — e.g. Pierce, Cover, or a reroll ability.

    Unlike a PassiveRule, an ActiveRule is never automatically in
    effect: it's only legal to invoke during its own `window`, and
    invoking it is a choice the decision engine makes, not a standing
    fact about the roll.
    """

    name: str
    """The rule's name, as written on the card (e.g. "Pierce").
    """

    window: Window
    """Which modification window this rule is legal in — see Window
    for the valid values and their order.
    """

    target: str | Sequence[str]
    """Which dice in the roll are eligible to be affected. Either a
    dynamic category ("any_failure", "any_success", "all") that reflects
    the *current* success/failure state of each die, or a literal list
    of named faces for rules that name specific faces on the card (e.g.
    Pierce's ["Critical", "Wild", "Shield"]) — literal lists don't shift
    even if a passive modifier changes what else counts as a success.
    """

    effect: str
    """What a targeted die becomes when this rule is applied — a
    resulting face name (e.g. "Shield" for Cover), or "reroll" for
    probabilistic modifications.
    """

    mode: Literal["deterministic", "probabilistic"]
    """"deterministic" (the effect is guaranteed) or "probabilistic"
    (the die is rerolled to a random result).
    """

    quantity: DiceModQuantity
    """Computes how many dice this rule's effect is scaled to. This is
    the formula's raw result only — see DiceModQuantity's own docstring
    for why it still needs to be clamped against target-matching,
    modifiable dice at resolution time.
    """

    temporary_overrides: Sequence[PropertyOverride] = \
        field(default_factory=tuple)
    """Property overrides that apply only while this specific rule is
    being executed, then revert immediately (e.g. "Skulls are
    modifiable for this reroll"). Distinct from a PassiveRule, which
    applies for the whole attack. Empty for rules that carry no such
    override, which is the common case.
    """


@dataclass(frozen=True, kw_only=True)
class PassiveRule:
    """A standing rule that's always in effect for a character
    throughout the entire attack sequence — not scoped to any
    modification window.

    Consulted anywhere a die's property is read: success tallying,
    explode-eligibility, target-matching for an ActiveRule, and so on.
    Because it has no window, a PassiveRule can affect either side's
    roll depending on what the override itself describes (e.g. "count
    opponent's Hit as success" reads from the opponent's roll even
    though the rule belongs to this character).
    """

    name: str
    """The rule's name, as written on the card (e.g. "Pierce").
    """

    override: PropertyOverride
    """The single property override this passive rule grants.
    """


@dataclass(frozen=True)
class Restriction:
    """Disables an entire modification window outright, regardless of
    what dice would otherwise be eligible (e.g. Prowler's "the
    defender cannot modify its defense dice"). No owner/applies_to
    field needed — Window values are already actor-specific.
    """
    disabled_windows: Sequence[Window]


def reroll_x_rule(
    name: str,
    window: Window,
    max_quantity: int | None,
    temporary_overrides: Sequence[PropertyOverride] | None = None,
) -> ActiveRule:
    """Builds a failure-only reroll ability — the character rerolls up
    to max_quantity of their own eligible failures (Skulls excluded
    unless a passive rule overrides their modifiability).

    max_quantity=None produces an uncapped failure-only reroll
    (equivalent to the doc's "Reroll Any").

    Args:
        name: Base label for the rule. The generated ActiveRule.name
            appends "(Reroll N)" or "(Reroll Any)".
        window: Which modification window this reroll is legal in.
        max_quantity: Upper limit on dice rerolled, or None for
            uncapped (Reroll Any).
        temporary_overrides: Property overrides that apply only while
            this specific reroll is being executed (e.g., Shadowland
            Daredevil's "may reroll a Skull" - doesn't unlock Skulls
            for any other rule). Defaults to None.

    Returns:
        The assembled ActiveRule.
    """
    label = "Any" if max_quantity is None else max_quantity
    return ActiveRule(
        name=f"{name} (Reroll {label})",
        window=window,
        target="any_failure",
        effect="reroll",
        mode="probabilistic",
        quantity=DiceModQuantity(max_quantity=max_quantity),
        temporary_overrides=temporary_overrides or [],
    )


def reroll_all_rule(
    name: str,
    window: Window,
    temporary_overrides: Sequence[PropertyOverride] | None = None,
) -> ActiveRule:
    """Builds a reroll-everything ability — every modifiable die in
    the roll is rerolled, successes and failures alike. Riskier than
    reroll_x_rule/reroll_any_rule, since it can undo existing
    successes; the decision engine needs real analysis (see the
    Darkstar EV-vs-dominance discussion) before invoking this, unlike
    the failure-only rerolls, which are always safe to use.

    Args:
        name: Base label for the rule. The generated ActiveRule.name
            appends "(Reroll N)" or "(Reroll Any)".
        window: Which modification window this reroll is legal in.
        temporary_overrides: Property overrides that apply only while
            this specific reroll is being executed (e.g., Shadowland
            Daredevil's "may reroll a Skull" - doesn't unlock Skulls
            for any other rule). Defaults to None.

    Returns:
        The assembeld ActiveRule.
    """
    return ActiveRule(
        name=name,
        window=window,
        target="all",
        effect="reroll",
        mode="probabilistic",
        quantity=DiceModQuantity(max_quantity=None),
        temporary_overrides=temporary_overrides or [],
    )


def reroll_any_rule(
    name: str,
    window: Window,
    temporary_overrides: Sequence[PropertyOverride] | None = None,
) -> ActiveRule:
    """Builds an uncapped, failure-only reroll ability — thin wrapper
    around reroll_x_rule with max_quantity=None. Safe to invoke
    whenever available, since it never touches existing successes.

    Args:
        name: Base label for the rule. The generated ActiveRule.name
            appends "(Reroll N)" or "(Reroll Any)".
        window: Which modification window this reroll is legal in.
        temporary_overrides: Property overrides that apply only while
            this specific reroll is being executed (e.g., Shadowland
            Daredevil's "may reroll a Skull" - doesn't unlock Skulls
            for any other rule). Defaults to None.

    Returns:
        The assembeld ActiveRule.
    """
    return reroll_x_rule(
        name=name,
        window=window,
        max_quantity=None,
        temporary_overrides=temporary_overrides or [],
    )


def pierce_rule(
    name: str,
    window: Window,
    target_faces: str | Sequence[str],
    quantity: DiceModQuantity,
) -> ActiveRule:
    """Builds a Pierce-family ability — changes an opponent's success
    to Blank. Covers every variant (plain Pierce, gated on a specific
    face via quantity.faces_to_count, or scaled/reversed like Energy
    Absorption) by taking the target faces and quantity formula as
    inputs rather than hardcoding either.

    Args:
        name: The rule's name, as written on the card (e.g. "Pierce",
            "Energy Absorption").
        window: Which modification window this rule is legal in
            (ATTACKER_MOD_DEFENDER for the standard direction,
            DEFENDER_MOD_ATTACKER for a reversed variant).
        target_faces: The specific faces eligible to be changed (e.g.
            ["Critical", "Wild", "Shield"] for the standard direction).
        quantity: The trigger/scaling formula for how many dice this
            can affect — fixed (plain Pierce), gated (Zemo's Wild
            requirement), or scaling (Energy Absorption).

    Returns:
        The assembled ActiveRule, with effect="Blank" and
        mode="deterministic".
    """
    return ActiveRule(
        name=name,
        window=window,
        target=target_faces,
        effect="Blank",
        mode="deterministic",
        quantity=quantity
    )
