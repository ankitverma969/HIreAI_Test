"""Tests for the similarity and scoring engine modules."""


from app.scorer.similarity_engine import (
    compute_cosine_similarity,
    compute_keyword_similarity,
    compute_skill_similarity,
)


class TestComputeCosineSimilarity:
    """Tests for the cosine similarity computation function."""

    def test_identical_vectors_returns_100(self):
        vec = [1.0, 0.5, 0.2, 0.8]
        result = compute_cosine_similarity(vec, vec)
        assert abs(result - 100.0) < 0.01

    def test_orthogonal_vectors_returns_0(self):
        vec_a = [1.0, 0.0]
        vec_b = [0.0, 1.0]
        result = compute_cosine_similarity(vec_a, vec_b)
        assert result == 0.0

    def test_zero_vector_returns_0(self):
        vec_a = [0.0, 0.0, 0.0]
        vec_b = [1.0, 2.0, 3.0]
        result = compute_cosine_similarity(vec_a, vec_b)
        assert result == 0.0

    def test_output_clamped_between_0_and_100(self):
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [4.0, 5.0, 6.0]
        result = compute_cosine_similarity(vec_a, vec_b)
        assert 0.0 <= result <= 100.0

    def test_similar_vectors_high_score(self):
        vec_a = [1.0, 1.0, 1.0]
        vec_b = [1.0, 1.0, 0.9]
        result = compute_cosine_similarity(vec_a, vec_b)
        assert result > 90.0


class TestComputeSkillSimilarity:
    """Tests for weighted skill similarity scoring."""

    def test_perfect_match_required_and_preferred(self):
        cand = ["python", "fastapi", "docker"]
        req = ["python", "fastapi"]
        pref = ["docker"]
        result = compute_skill_similarity(cand, req, pref)
        assert result == 100.0

    def test_no_required_no_preferred_returns_100(self):
        result = compute_skill_similarity(["python"], [], [])
        assert result == 100.0

    def test_zero_match_returns_0(self):
        cand = ["java", "spring"]
        req = ["python", "fastapi", "docker"]
        pref = ["kubernetes"]
        result = compute_skill_similarity(cand, req, pref)
        assert result == 0.0

    def test_partial_match_preferred_weighted_half(self):
        # required=["python"], preferred=["docker"]
        # candidate only has preferred "docker", not required "python"
        cand = ["docker"]
        req = ["python"]
        pref = ["docker"]
        result = compute_skill_similarity(cand, req, pref)
        # matched_weight = 0.5 (preferred docker), total = 1.0 + 0.5 = 1.5
        # expected = (0.5 / 1.5) * 100 = 33.33
        assert abs(result - 33.33) < 0.5

    def test_case_insensitive_matching(self):
        cand = ["Python", "FASTAPI"]
        req = ["python", "fastapi"]
        pref = []
        result = compute_skill_similarity(cand, req, pref)
        assert result == 100.0

    def test_result_always_in_valid_range(self):
        result = compute_skill_similarity(["go", "rust"], ["python", "java", "scala"], [])
        assert 0.0 <= result <= 100.0


class TestComputeKeywordSimilarity:
    """Tests for keyword Jaccard overlap scoring."""

    def test_perfect_keyword_overlap(self):
        keywords = ["machine learning", "nlp", "python"]
        result = compute_keyword_similarity(keywords, keywords)
        assert result == 100.0

    def test_no_jd_keywords_returns_100(self):
        result = compute_keyword_similarity(["python"], [])
        assert result == 100.0

    def test_no_overlap_returns_0(self):
        cand = ["java", "spring"]
        jd = ["python", "fastapi"]
        result = compute_keyword_similarity(cand, jd)
        assert result == 0.0

    def test_partial_overlap(self):
        cand = ["python", "django"]
        jd = ["python", "fastapi", "docker"]
        result = compute_keyword_similarity(cand, jd)
        # overlap={"python"}, jd_set size=3
        # expected = 1/3 * 100 = 33.33
        assert abs(result - 33.33) < 0.5

    def test_case_insensitive(self):
        cand = ["Python", "FastAPI"]
        jd = ["python", "fastapi"]
        result = compute_keyword_similarity(cand, jd)
        assert result == 100.0
