# MCP Dice

## Dice Faces

| Face | Attack | Defense | Dodge | Notes |
| --- | --- | --- | --- | --- |
| Critical | Success | Success | Success | Critcals add dice during attack, defense, and dodge rolls. |
| Wild | Success | Success | Success | |
| Hit | Success | Failure | Failure | |
| Hit | Success | Failure | Failure | |
| Shield | Failure | Success | Success | |
| Blank | Failure | Failure | Failure | |
| Blank | Failure | Failure | Failure | |
| Skull | Failure | Failure | Failure | Skulls can't be rerolled or modified. |

## Attack Sequence

1. Create the attackers dice pool.
2. Create the defenders dice pool.
3. Roll the attackers dice pool. This is the attack roll.
4. Roll the defenders dice pool. This is the defense roll.
5. Resolve *Criticals* rolled.
   1. The attacker rolls an addtional dice for each *Critical* in the original attack roll.
   2. The defender rolls an additional dice for each *Critical* in the original defense roll
6. Player's modify their dice.
   1. The attacker applies rerolls and effects that change the attacker's die results to the attack roll.
   2. The defender applies rerolls and effects that change the attacker's die results to the defense roll.
7. Player's modify their opponent's dice.
   1. The attacker applies rerolls and effects that change the defender's die results to the defense roll.
   2. The defender applies rerolls and effects that change the attacker's die results to the attack roll.
8. Calclate success or failure.
   1. Total the number of the attacker's Criticals, Wilds, and Hits. This is the number of the attacker's successes.
   2. Total teh number of the defender's Criticals, Wilds, and Shields. This is the number of the defender's successes.
   3. Subtract the total number of the defender's successes from the total number of the attacker's successes. If the result is 0 or less, the attack is a failure. If the result is greater than 0, the attack is a hit. The remaining number of successes is the amount of damage the attack will deal in the *Apply Damage* step.

## Dice Effects (not modifications)

- Hex - Don't add additional dice for criticals.
- Modify Skulls - Special rule that does allow for skull results to be modifided.
- Count [insert dice face] as Success - Special rule that allows dice faces that would normally be a failure as a sucess (e.g., count blanks will include blank faces in the total number of succeses).
- Count [insert dice face] as Failure - Spacial rule that does not allow a dice faces that would normally be a success to be a failure (e.g., critical are not counted as successes).
- Count Opponents [insert dice face] as Success - Special rules that adds the number of the specified dice face in the opponents roll to player's total successes.
- [insert dice face] is not a success - Special rule that that treats a dice face as a failure that would normally be a success.
- Damage if Defender Has a *Skull* - Special rule that allows causes one additinal damage to the defender if their defense roll contained one or more *Skull* results.

## Dice Modifications

Players may apply dice modifications in any order they desire within the designated timing step as described in steps 6 and 7 of the Attack Sequence.

When a rule instructs a player to modify a dice, they player will typically only apply modifications that will benefit the player. If a player may modify their own dice, they will modify failure results. If a player may modify their opponents dice, they will modify success results.

### Rerolls

When a rule instructs a player to reroll a dice, that dice will be rerolled result in a random result.

- Reroll All - Reroll all dice, both successes and failures, except *Skulls*.
- Reroll Any - Reroll all failures, except *Skulls*.
- Reroll X - Reroll 0 to X dice, reroll failures, except *Skulls*.
- Witty Banter - The defender rerolls up to 1 of the attacker's successes.
- Disruption Field - The defender rerolls up to 2 of the attacer's successes.
- Oscorp Weaponry - The attacker rerolls up to 1 of the defender's successes.

### Specific Dice Modifications

Specific dice modifications are rules that will explicitly change a die to a specific result.

- Pierce on [insert dice face(s)] - The attacker may change one of the defender's success to a *Blank* die face.
- Special Forces / Super Genius (if better) - Special rule that is applied during the *Calculate Success* step of the attack, this character counts *Shield* results instead of *Hit* results as successes.
- Wild Modify 1 to Hit - If an attack roll contains at least one *Wild* result, the attacker may change one failure to a *Hit*.
- Wild Modify 1 to Shield - If a defense roll contains at least one *Wild* result, the defender may change one failure to a *Shield*.
- Warrior of Legend - Special rule that allows the attacker to change 1 failure to a *Hit* for each *Critical* or *Wild* in the attack role.
- Death Dancer (Attacker) - Special rule that allows the attacker to change 1 failure to a *Hit* for each *Critical* in the opposing defense roll.
- Death Dancer (Defender) - Special rule that allows the defender to change 1 failure to a *Shield* for each *Critical* in the opposing attack roll.
- Cover - Special rule that allows the defender to change 1 failure to a *Shield*.
- Energy Absorbption - Special rule that allows the defender to change 1 *Hit*, *Critical*, or *Wild* in the attack roll for each *Wild* n the defense roll.
- Attackers Wilds to Blanks - Special rule that allows teh defender to change all *Wild* results in the attack role to *Blank* results.

## Calculate Successes

- Count [insert dice face] as [insert number] Successes - Special rule that allows a specific dice face to count as multiple successes (e.g. when this character is attacking, each *Wild* in its roll counts as 2 successes).

## Apply Damage

1. The defending charcter suffers Damage from attack (see step 8.3 above).
2. Apply any special rules that reduce the damage suffered.
   1. Reduce by 1 - When this character would suffer 1 or more damage from an enemy effect, reduce the amount of damage suffered by 1.
   2. Reduce by 1, to a minimum of 1 - When this character would suffer damage from an enemy effect, reduce the amount of damage suffered by 1, to a minimum of 1.
