def get_next_difficulty(current, is_correct):
    transitions = {
        'easy': ('medium', 'easy'),
        'medium': ('hard', 'easy'),
        'hard': ('hard', 'medium')
    }

    if current not in transitions:
        return 'easy'

    next_if_true, next_if_false = transitions[current]
    return next_if_true if is_correct else next_if_false