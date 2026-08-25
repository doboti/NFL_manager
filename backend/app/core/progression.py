"""Manager progression: level (from completed seasons, across every team
the manager has ever owned) and how many league "slots" that unlocks.
Computed on the fly, same philosophy as achievements.py -- no stored,
sync-able level field."""

# slot number -> minimum level required to unlock it. Slot 1 is always open.
SLOT_LEVEL_REQUIREMENTS = {1: 1, 2: 5, 3: 15}


def compute_level(completed_seasons: int) -> int:
    return 1 + completed_seasons


def unlocked_slots(level: int) -> int:
    return sum(1 for required in SLOT_LEVEL_REQUIREMENTS.values() if level >= required)


def next_slot_requirement(level: int) -> dict | None:
    """The next locked slot's level requirement, or None if all are unlocked."""
    locked = sorted(
        (slot, required) for slot, required in SLOT_LEVEL_REQUIREMENTS.items() if level < required
    )
    if not locked:
        return None
    slot, required = locked[0]
    return {"slot": slot, "required_level": required}
