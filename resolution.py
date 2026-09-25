import random
from collections.abc import Sequence

from dice_model import face_lookup, mcp_dice
from rules import ActiveRule, DiceModQuantity, PassiveRule


def merge_temporary_overrides(
    passive_rules: Sequence[PassiveRule],
    rule: ActiveRule
) -> list[PassiveRule]:
    """Combines passive rules with temporary overrides into a single
    list to be used when making dice modifications.
    """
    return list(passive_rules) + [
        PassiveRule(
            name=f"Temp_{rule.name}",
            override=temp
        )
        for temp in rule.temporary_overrides
    ]


def effective_modifiable(
        face_name: str,
        passive_rules: Sequence[PassiveRule],
) -> bool:
    """Resolves whether a face is modifiable, starting from its base
    DieFace.is_modifiable and applying any matching passive-rule
    override (e.g. Miles Morales's Modify Skulls).
    """
    modifiable = face_lookup[face_name].is_modifiable
    for rule in passive_rules:
        properties = rule.override.property
        props_to_check = (
            [properties] if isinstance(properties, str)
            else properties
        )

        if (
            rule.override.face == face_name
            and "is_modifiable" in props_to_check
        ):
            modifiable = bool(rule.override.effect)

    return modifiable


def apply_reroll(
        roll: Sequence[str],
        results: Sequence[int],
        rule: ActiveRule,
        passive_rules: Sequence[PassiveRule],
) -> list[str]:
    """Applies a probabilistic reroll to a roll, honoring rule.target
    and rule.quantity.

    Finds eligible positions — matching rule.target ("any_failure" for
    reroll_x_rule/reroll_any_rule, "all" for reroll_all_rule) and
    modifiable once passive_rules and rule.temporary_overrides are
    accounted for — then rerolls up to rule.quantity.max_quantity of
    them (or every eligible position, if uncapped). Returns a new
    list; roll is not mutated.

    Args:
        roll: The current roll (face names) to reroll from.
        results: Each position's current success value, same order
            as roll.
        rule: The reroll ActiveRule being applied.
        passive_rules: The roll owner's standing passive rules.

    Returns:
        A new roll list with eligible positions rerolled.
    """
    combined_rules = merge_temporary_overrides(
        passive_rules=passive_rules,
        rule=rule
    )

    eligible_positions = [
        i for i, (face_name, value) in enumerate(zip(roll, results))
        if face_matches_target(face_name, value, rule.target)
        and effective_modifiable(face_name, combined_rules)
    ]

    if rule.quantity.max_quantity is None:
        reroll_count = len(eligible_positions)
    else:
        reroll_count = min(rule.quantity.max_quantity, len(eligible_positions))

    updated_roll = list(roll)

    if reroll_count > 0:
        new_faces = random.choices(mcp_dice, k=reroll_count)
        for position, face in zip(
            eligible_positions[:reroll_count], new_faces
        ):
            updated_roll[position] = face

    return updated_roll


def resolve_quantity(
        quantity_rule: DiceModQuantity,
        own_roll: Sequence[str],
        opponent_roll: Sequence[str]
) -> int | None:
    """Resolves a DiceModQuantity's formula against real rolls, returning
    the raw number of dice this rule's effect is scaled to.

    Returns None specifically when there's no formula at all AND no cap
    (faces_to_count is None and max_quantity is None) — e.g. Reroll All —
    signaling the caller should clamp against however many dice are
    actually eligible, rather than against a fixed number.
    """
    if quantity_rule.faces_to_count is None:
        raw = None
    else:
        source_roll = (
            own_roll
            if quantity_rule.source_roll == "own"
            else opponent_roll
        )
        counts = [source_roll.count(face)
                  for face in quantity_rule.faces_to_count]

        if quantity_rule.matching_rule == "all":
            raw = (
                quantity_rule.coefficient
                if all(c >= 1 for c in counts)
                else 0
            )
        else:  # "any"
            raw = quantity_rule.coefficient * sum(counts)

    if quantity_rule.max_quantity is None:
        return raw  # None (Reroll All) or the uncapped formula result

    if raw is None:
        return quantity_rule.max_quantity  # fixed use, no formula

    return min(quantity_rule.max_quantity, raw)  # gated or capped-scaling


def face_matches_target(
        face_name: str,
        value: int,
        target: str | Sequence[str]
) -> bool:
    """True if a die qualifies for rule.target (a face list or a
    dynamic category)."""
    # 1. Handle literal collections of face names first
    if not isinstance(target, str):
        return face_name in target

    # 2. Handle string-based dynamic categories cleanly
    match target:
        case "any_failure":
            return value == 0
        case "any_success":
            return value > 0
        case "all":
            return True
        case _:
            return False


def apply_deterministic_mod(
    target_roll: Sequence[str],
    target_results: Sequence[int],
    rule: ActiveRule,
    own_roll: Sequence[str],
    opponent_roll: Sequence[str],
    passive_rules: Sequence[PassiveRule],
) -> list[str]:
    """Applies a deterministic rule (Pierce, Cover) to target_roll.
    own_roll/opponent_roll belong to the rule's OWNER (for the trigger
    check); passive_rules belong to the TARGET's owner (for modifiability).
    """

    combined_rules = merge_temporary_overrides(
            passive_rules=passive_rules,
            rule=rule
        )

    # 1. Trigger check — does the owner's roll satisfy the rule's formula?
    trigger_count = resolve_quantity(
        quantity_rule=rule.quantity,
        own_roll=own_roll,
        opponent_roll=opponent_roll
    )
    if trigger_count == 0:  # doesn't have trigger return original
        return list(target_roll)

    # 2. Target check — which of target_roll's dice are eligible?
    eligible_positions = [
        i for i, (face_name, value) in enumerate(
            zip(target_roll, target_results)
            )
        if face_matches_target(face_name, value, rule.target)
        and effective_modifiable(face_name, combined_rules)
    ]

    # 3. Apply to the first N eligible (N = trigger_count, or all if uncapped)
    apply_count = (
        len(eligible_positions)
        if trigger_count is None
        else min(trigger_count, len(eligible_positions))
    )

    updated_roll = list(target_roll)
    for position in eligible_positions[:apply_count]:
        updated_roll[position] = rule.effect

    return updated_roll
