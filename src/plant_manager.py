"""
Plant growth stage logic based on currency milestones.
"""
# Dewdrop milestones for each stage (inclusive lower bound)
# Stages 0-5: 0, 100, 200, 300, 400, 500+
MILESTONES = (0, 100, 200, 300, 400, 500)


def get_stage_from_currency(balance: int) -> int:
    """
    Return plant stage (0-5) for a given dewdrop balance.
    Milestones: 0, 100, 200, 300, 400, 500.
    """
    stage = 0
    for i, milestone in enumerate(MILESTONES):
        if balance >= milestone:
            stage = i
    return min(stage, 5)
