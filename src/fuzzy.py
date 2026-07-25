"""
Fuzzy Subsequence Matching & Scoring Engine for weg (Phase 8.4).
Powers live filter '/' and recursive search '>'.
"""

def fuzzy_match(pattern, target):
    """
    Returns (matched: bool, score: float).
    Subsequence matching: characters in pattern must appear in target in order.
    """
    if not pattern:
        return True, 0.0

    pattern_lower = pattern.lower()
    target_lower = target.lower()

    p_idx = 0
    p_len = len(pattern_lower)
    t_len = len(target_lower)

    last_match_idx = -10
    score = 0.0
    consecutive_bonus = 0.0

    for t_idx, ch in enumerate(target_lower):
        if p_idx < p_len and ch == pattern_lower[p_idx]:
            # Base match score
            score += 10.0

            # Consecutive match bonus
            if t_idx == last_match_idx + 1:
                consecutive_bonus += 5.0
                score += consecutive_bonus
            else:
                consecutive_bonus = 0.0

            # Boundary match bonus (start of string, after /, _, -, ., space, or camelCase)
            if t_idx == 0 or target[t_idx - 1] in "/_-. " or (target[t_idx].isupper() and target[t_idx - 1].islower()):
                score += 15.0

            last_match_idx = t_idx
            p_idx += 1

    if p_idx == p_len:
        # Length penalty: shorter target string is preferred
        score -= (t_len - p_len) * 0.1
        return True, score

    return False, 0.0

def fuzzy_filter_items(items, query, key_fn=lambda item: item.name):
    """
    Filters and ranks items using fuzzy_match algorithm.
    """
    if not query:
        return items

    matched_results = []
    for item in items:
        target_str = key_fn(item)
        matched, score = fuzzy_match(query, target_str)
        if matched:
            matched_results.append((score, item))

    # Sort descending by fuzzy score
    matched_results.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in matched_results]
