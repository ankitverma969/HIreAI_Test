from loguru import logger

from app.embeddings.generator import SentenceTransformerGenerator
from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.score import Score, ScoreBreakdown
from app.scorer.interface import BaseCandidateScorer
from app.scorer.similarity_engine import (
    compute_cosine_similarity,
    compute_keyword_similarity,
    compute_skill_similarity,
)


class CandidateScorer(BaseCandidateScorer):
    """Calculates weighted rule-based match scores and confidence ratings for candidates."""

    def __init__(self, embedding_generator: SentenceTransformerGenerator):
        """Initializes the scorer with a vector embedding generator.

        Args:
            embedding_generator: Dense vector generator instance.
        """
        self.generator = embedding_generator

    def calculate_score(self, candidate: Candidate, jd: JobDescription) -> Score:
        """Calculates candidate matching scores against job requirements.

        Args:
            candidate: Structured candidate profile.
            jd: Target job description.

        Returns:
            Calculated score containing breakdown and matching metrics.
        """
        logger.info(f"Scoring candidate '{candidate.full_name}' against Job Description '{jd.title}'")

        # 1. Skill Match Score ( Jaccard / Weight overlap ) - 35% weight
        skill_score = compute_skill_similarity(
            candidate_skills=candidate.skills,
            required_skills=jd.required_skills,
            preferred_skills=jd.preferred_skills
        )

        # Identify matched and missing skills lists
        set(s.lower().strip() for s in jd.required_skills)
        cand_set = set(s.lower().strip() for s in candidate.skills)
        matched_skills = [s for s in jd.required_skills if s.lower().strip() in cand_set]
        missing_skills = [s for s in jd.required_skills if s.lower().strip() not in cand_set]

        # 2. Keyword Match Score (Jaccard on all keywords)
        keyword_score = compute_keyword_similarity(
            candidate_keywords=candidate.skills,  # Match candidate skills list as candidate keyword pool
            jd_keywords=jd.keywords
        )

        # Generate text block embeddings for vector comparisons
        jd_text = jd.raw_content
        jd_emb = self.generator.generate_embedding(jd_text)

        # Experience text block match - 25% weight
        # Concatenate candidate experience roles/responsibilities
        exp_texts = []
        for exp in candidate.experience:
            exp_texts.append(f"{exp.role} at {exp.company}: {exp.responsibilities or ''}")
        exp_text = " ".join(exp_texts)

        exp_cosine = 0.0
        if exp_text.strip():
            exp_emb = self.generator.generate_embedding(exp_text)
            exp_cosine = compute_cosine_similarity(exp_emb, jd_emb)

        # Years match factor (0.0 to 100.0)
        years_factor = 100.0
        if jd.minimum_experience_years is not None and jd.minimum_experience_years > 0:
            if candidate.total_experience_years < jd.minimum_experience_years:
                years_factor = (candidate.total_experience_years / jd.minimum_experience_years) * 100.0

        # Combine experience cosine alignment and years match
        experience_score = (exp_cosine * 0.6) + (years_factor * 0.4)

        # Projects text block match - 15% weight
        proj_texts = []
        for proj in candidate.projects:
            proj_texts.append(f"{proj.project_name}: {proj.description or ''} using {', '.join(proj.technologies_used)}")
        proj_text = " ".join(proj_texts)

        project_score = 0.0
        if proj_text.strip():
            proj_emb = self.generator.generate_embedding(proj_text)
            project_score = compute_cosine_similarity(proj_emb, jd_emb)

        # Education text block match - 10% weight
        edu_texts = []
        for edu in candidate.education:
            edu_texts.append(f"{edu.degree} from {edu.university or edu.college or ''}")
        edu_text = " ".join(edu_texts)

        edu_cosine = 0.0
        if edu_text.strip():
            edu_emb = self.generator.generate_embedding(edu_text)
            edu_cosine = compute_cosine_similarity(edu_emb, jd_emb)

        # Academic Degree Requirement match factor (0.0 to 100.0)
        degree_factor = 50.0
        if not jd.education_requirements:
            degree_factor = 100.0
        else:
            cand_degrees = set(e.degree.lower().strip() for e in candidate.education if e.degree)
            jd_reqs = set(req.lower().strip() for req in jd.education_requirements)
            if cand_degrees & jd_reqs:
                degree_factor = 100.0

        education_score = (edu_cosine * 0.5) + (degree_factor * 0.5)

        # Certifications match - 5% weight
        certification_score = 0.0
        if candidate.certifications:
            # Baseline score if they have any certifications
            certification_score = 50.0
            # Scale up to 100 if certification text aligns with JD
            cert_texts = [c.certification_name for c in candidate.certifications if c.certification_name is not None]
            cert_text = " ".join(cert_texts)
            cert_emb = self.generator.generate_embedding(cert_text)
            cert_cosine = compute_cosine_similarity(cert_emb, jd_emb)
            certification_score = (certification_score * 0.5) + (cert_cosine * 0.5)

        # Overall Semantic Cosine Similarity - 10% weight
        cand_raw_emb = self.generator.generate_embedding(candidate.raw_resume_text)
        semantic_similarity = compute_cosine_similarity(cand_raw_emb, jd_emb)

        # 3. Calculate Overall Weighted Score
        # Weights:
        # Skills: 35%, Experience: 25%, Projects: 15%, Education: 10%, Semantic Similarity: 10%, Certifications: 5%
        overall_score = (
            (skill_score * 0.35) +
            (experience_score * 0.25) +
            (project_score * 0.15) +
            (education_score * 0.10) +
            (semantic_similarity * 0.10) +
            (certification_score * 0.05)
        )

        # 4. Calculate Confidence Score (0-100)
        confidence_score = self.calculate_confidence_score(candidate, semantic_similarity, skill_score)

        # Compile breakdown
        breakdown = ScoreBreakdown(
            skill_match=float(round(skill_score, 1)),
            keyword_match=float(round(keyword_score, 1)),
            experience_match=float(round(experience_score, 1)),
            project_match=float(round(project_score, 1)),
            education_match=float(round(education_score, 1)),
            certification_match=float(round(certification_score, 1)),
            semantic_similarity=float(round(semantic_similarity, 1))
        )

        # Construct qualitative scorer explanation reasoning
        reasoning = (
            f"The candidate '{candidate.full_name}' achieved an overall weighted score of {overall_score:.1f}% "
            f"with a scoring confidence of {confidence_score:.1f}%. "
            f"Skills alignment is scored at {skill_score:.1f}%, while professional experience alignment "
            f"is evaluated at {experience_score:.1f}% based on {candidate.total_experience_years:.1f} years of total history."
        )

        logger.info(f"Scoring completed for candidate '{candidate.full_name}': Score={overall_score:.2f}%")

        return Score(
            overall_score=float(round(overall_score, 1)),
            breakdown=breakdown,
            confidence_score=float(round(confidence_score, 1)),
            reasoning=reasoning,
            matched_skills=matched_skills,
            missing_skills=missing_skills
        )

    def calculate_confidence_score(
        self,
        candidate: Candidate,
        semantic_sim: float,
        skill_sim: float
    ) -> float:
        """Computes score confidence ratings out of 100 based on metadata quality attributes.

        Uses:
        1. Data Completeness (email, phone, location, linkedin, portfolio, summary fields)
        2. Resume Quality (experience records count and word size)
        3. Extraction confidence (validated email structure presence)
        4. Similarity consistency (variance/proximity of semantic similarity vs skill similarity)
        """
        # 1. Data Completeness (20 points max)
        completeness_checks = [
            candidate.email is not None,
            candidate.phone is not None,
            candidate.location is not None,
            candidate.linkedin is not None,
            candidate.summary is not None
        ]
        completeness = sum(20 for val in completeness_checks if val)

        # 2. Resume Quality (100 points max, scaled to 30 points weight)
        quality_score = 0.0
        if len(candidate.experience) >= 2:
            quality_score = 100.0
        elif len(candidate.experience) == 1:
            quality_score = 70.0
        else:
            quality_score = 30.0

        # Add word size check
        word_count = len(candidate.raw_resume_text.split())
        if 150 <= word_count <= 800:
            quality_score = (quality_score * 0.8) + 20.0
        else:
            quality_score = quality_score * 0.8

        # 3. Extraction Confidence (100 points max, scaled to 25 points weight)
        extraction_conf = 50.0
        if candidate.email and candidate.phone:
            extraction_conf = 100.0
        elif candidate.email or candidate.phone:
            extraction_conf = 80.0

        # 4. Similarity consistency (100 points max, scaled to 25 points weight)
        # Low variance between general semantic alignment and strict skills Jaccard match = high consistency
        variance = abs(semantic_sim - skill_sim)
        similarity_consistency = max(0.0, 100.0 - (variance * 1.5))

        # Aggregate with weights
        # Completeness: 20%, Quality: 30%, Extraction: 25%, Consistency: 25%
        confidence = (
            (completeness * 0.20) +
            (quality_score * 0.30) +
            (extraction_conf * 0.25) +
            (similarity_consistency * 0.25)
        )

        return float(max(0.0, min(100.0, confidence)))
