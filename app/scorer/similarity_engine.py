
import numpy as np


def compute_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Computes cosine similarity between two dense vectors and scales it to 0-100.

    Args:
        vec_a: First float vector.
        vec_b: Second float vector.

    Returns:
        Normalized score in range 0.0 to 100.0.
    """
    a = np.array(vec_a)
    b = np.array(vec_b)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    dot_product = np.dot(a, b)
    similarity = dot_product / (norm_a * norm_b)

    # Cosine is in range [-1.0, 1.0]. Normalize to 0-100.
    # Text vectors are usually non-negative, so we clip between 0.0 and 100.0.
    return float(max(0.0, min(100.0, similarity * 100.0)))


def compute_skill_similarity(
    candidate_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str]
) -> float:
    """Calculates weighted skill overlap score between candidate and JD requirements.

    Required skills carry 1.0 weight, preferred skills carry 0.5 weight.

    Args:
        candidate_skills: List of candidate skills.
        required_skills: List of required skills from JD.
        preferred_skills: List of preferred skills from JD.

    Returns:
        Weighted similarity score out of 100.
    """
    if not required_skills and not preferred_skills:
        return 100.0  # Matches perfectly if job has no skills defined

    cand_set = set(s.lower().strip() for s in candidate_skills)
    req_set = [s.lower().strip() for s in required_skills]
    pref_set = [s.lower().strip() for s in preferred_skills]

    total_possible_weight = len(req_set) * 1.0 + len(pref_set) * 0.5
    if total_possible_weight == 0.0:
        return 100.0

    matched_weight = (
        sum(1.0 for s in req_set if s in cand_set) +
        sum(0.5 for s in pref_set if s in cand_set)
    )

    return float(max(0.0, min(100.0, (matched_weight / total_possible_weight) * 100.0)))


def compute_keyword_similarity(
    candidate_keywords: list[str],
    jd_keywords: list[str]
) -> float:
    """Calculates keyword Jaccard overlap normalized to 0-100.

    Args:
        candidate_keywords: Semantic keywords list from candidate.
        jd_keywords: Target keywords from JD.

    Returns:
        Match score in range 0.0 to 100.0.
    """
    if not jd_keywords:
        return 100.0

    cand_set = set(k.lower().strip() for k in candidate_keywords)
    jd_set = set(k.lower().strip() for k in jd_keywords)

    overlap = cand_set & jd_set
    if not jd_set:
        return 100.0

    return float(max(0.0, min(100.0, (len(overlap) / len(jd_set)) * 100.0)))
