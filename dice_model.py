"""Core dice model for the MCP simulator: face definitions, the
sampling pool used for rolling, and a name-to-DieFace lookup table.

Every other module builds on face_lookup and mcp_dice — this file
should rarely need to change.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True, kw_only=True)
class DieFace:
    """One of the six unique face types on the 8-sided MCP die.
    Frozen because these are fixed rule-table constants — nothing
    should mutate a shared instance once created.
    """
    name: str
    """The face's name, matching its display name in the rules (e.g.
    "Wild", "Skull")."""

    attack_value: int = 0
    """Base success value when this face appears in an attack roll,
    before any passive rule overrides."""

    defense_value: int = 0
    """Base success value when this face appears in a defense roll."""

    dodge_value: int = 0
    """Base success value when this face appears in a dodge roll."""

    additional_dice: int = 0
    """How many bonus dice this face grants when it appears in an
    original roll (core rules grant Critical 1 additional die)."""

    is_modifiable: bool = True
    """Whether this face can be rerolled or changed by a modification,
    before any passive rule overrides (core rules only prevent a
    Skull result from being modified."""

    quantity: int = 1
    """How many of the 8 physical die sides show this face."""


class MCPFace(Enum):
    """Enumeration of all valid MCP dice faces for strict typing
    across the program"""

    HIT = DieFace(
        name="Hit",
        attack_value=1,
        quantity=2
    )

    CRITICAL = DieFace(
        name="Critical",
        attack_value=1,
        defense_value=1,
        dodge_value=1,
        additional_dice=1
    )

    WILD = DieFace(
        name="Wild",
        attack_value=1,
        defense_value=1,
        dodge_value=1
    )

    SHIELD = DieFace(
        name="Shield",
        defense_value=1,
        dodge_value=1
    )

    BLANK = DieFace(
        name="Blank",
        quantity=2
    )

    SKULL = DieFace(
        name="Skull",
        is_modifiable=False
    )


# list of all faces on a MCP die (don't include frequency)
all_faces: Sequence[DieFace] = [face.value for face in MCPFace]

# Derived from all_faces — don't hand-type mcp_dice or face_lookup
# separately, or they can drift out of sync with the face instances.
mcp_dice: Sequence[str] = [
    face.name
    for face in all_faces
    for _ in range(face.quantity)
]

# Generate lookup table via dictionary comprehension
face_lookup: Mapping[str, DieFace] = {
    face.name: face for face in all_faces
}
