import asyncio
import time
from datetime import datetime
from pathlib import Path

from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel, Field

from app.core.config import settings
from app.embeddings.generator import SentenceTransformerGenerator
from app.extractor.candidate_extractor import CandidateExtractor
from app.extractor.job_description_extractor import JobDescriptionExtractor
from app.graph.state import AgentState
from app.llm.client import get_llm_client
from app.models.candidate import Candidate
from app.models.report import Report
from app.models.score import Ranking, Score, ScoreBreakdown
from app.parser.parser_service import ParserService
from app.prompts.loader import PromptLoader
from app.scorer.scoring_engine import CandidateScorer
from app.scorer.similarity_engine import (
    compute_cosine_similarity,
)
from app.utils.text_cleaner import clean_text


class LLMAnalysisResult(BaseModel):
    """Pydantic model representing structured candidate analysis results from LLM."""
    strengths: list[str] = Field(description="Key strengths matching the job requirements")
    weaknesses: list[str] = Field(default_factory=list, description="Candidate gaps or weaknesses relative to the role")
    missing_skills: list[str] = Field(description="Required technical skills from job description that are missing")
    interview_questions: list[str] = Field(description="Exactly 5 custom questions to probe candidate's gaps, projects, or experience")
    learning_recommendations: list[str] = Field(description="Tailored study topics to bridge candidate gaps")
    hiring_summary: str = Field(description="Qualitative summary explanation of their suitability")
    recommendation: str = Field(description="Hiring suggestion: one of 'Strong Hire', 'Hire', 'Consider', 'Review', 'Reject'")


# 1. Validate Input Node
def validate_input_node(state: AgentState) -> AgentState:
    """Validates that initial inputs are present."""
    start_time = time.perf_counter()
    errors = []

    jd_path = state.get("job_description_path")
    jd_raw = state.get("job_description_raw")
    jd_obj = state.get("job_description")

    if not jd_path and not jd_raw and not jd_obj:
        errors.append("Invalid Input: Job Description must be provided via path, raw text, or structured object.")

    res_paths = state.get("resumes_paths")
    cand_input = state.get("candidates_input")
    cand_objs = state.get("candidates")

    if not res_paths and not cand_input and not cand_objs:
        errors.append("Invalid Input: Candidates list must be provided via paths, objects, or populated state.")

    duration = time.perf_counter() - start_time
    timing = dict(state.get("timing") or {})
    timing["validate_input"] = duration

    return {
        **state,
        "errors": errors,
        "timing": timing
    }


# Conditional Edge router
def should_continue(state: AgentState) -> str:
    """Decides if graph workflow can proceed based on validation state."""
    if state.get("errors"):
        logger.warning(f"Aborting graph workflow execution due to validation check issues: {state['errors']}")
        return "end"
    return "continue"


# 2. Parse Job Description Node
async def parse_jd_node(state: AgentState) -> AgentState:
    """Parses Job Description if not already parsed."""
    start_time = time.perf_counter()
    errors = []
    jd = state.get("job_description")

    if jd is None:
        try:
            raw_text = ""
            jd_path = state.get("job_description_path")
            jd_raw = state.get("job_description_raw")

            if jd_path:
                path = Path(jd_path)
                logger.info(f"Ingesting JD from file: {path.name}")
                parsed_res = await ParserService.parse_document(path)
                raw_text = parsed_res["cleaned_text"]
            elif jd_raw:
                logger.info("Ingesting raw Job Description text")
                raw_text = clean_text(jd_raw)

            if not raw_text.strip():
                raise ValueError("Job description raw text content is empty or unreadable.")

            jd = JobDescriptionExtractor.extract_job_description(
                "JD-" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                raw_text
            )
        except Exception as e:
            logger.error(f"JD Ingestion failed: {str(e)}")
            errors.append(f"JD Parsing Error: {str(e)}")

    duration = time.perf_counter() - start_time
    timing = dict(state.get("timing") or {})
    timing["parse_jd"] = duration

    return {
        **state,
        "job_description": jd,
        "errors": errors,
        "timing": timing
    }


# 3. Load Resumes Node
async def load_resumes_node(state: AgentState) -> AgentState:
    """Loads and extracts Candidates list."""
    start_time = time.perf_counter()
    errors = []
    candidates = list(state.get("candidates") or [])

    if not candidates:
        cand_input = state.get("candidates_input") or []
        res_paths = state.get("resumes_paths") or []

        if cand_input:
            logger.info(f"Loading {len(cand_input)} candidate entities directly from memory")
            candidates = cand_input
        elif res_paths:
            logger.info(f"Parsing and extracting {len(res_paths)} resume files in parallel")

            async def process_resume_path(path_str: str) -> Candidate | None:
                try:
                    path = Path(path_str)
                    parsed_res = await ParserService.parse_document(path)
                    cand = await CandidateExtractor.extract_candidate_profile(parsed_res)
                    return cand
                except Exception as ex:
                    logger.error(f"Failed to process resume '{path_str}': {str(ex)}")
                    errors.append(f"Resume extraction error '{path_str}': {str(ex)}")
                    return None

            tasks = [process_resume_path(p) for p in res_paths]
            results = await asyncio.gather(*tasks)
            candidates = [c for c in results if c is not None]

    duration = time.perf_counter() - start_time
    timing = dict(state.get("timing") or {})
    timing["load_resumes"] = duration

    return {
        **state,
        "candidates": candidates,
        "errors": errors,
        "timing": timing
    }


# 4. Generate Embeddings Node
def embedding_generation_node(state: AgentState) -> AgentState:
    """Generates batch embeddings for candidates and JD text segments using SentenceTransformers."""
    start_time = time.perf_counter()
    errors = []

    jd = state.get("job_description")
    candidates = state.get("candidates") or []

    jd_embedding = None
    cand_embs = {}
    exp_embs = {}
    proj_embs = {}
    edu_embs = {}

    if jd and candidates:
        try:
            generator = SentenceTransformerGenerator()
            logger.info("Generating JD text embedding vector")
            jd_embedding = generator.generate_embedding(jd.raw_content)

            # Prepare batch parameters for parallelized SentenceTransformer encoding
            texts_pool = []
            pool_keys = []

            for c in candidates:
                # Raw text
                texts_pool.append(c.raw_resume_text)
                pool_keys.append((c.id, "raw"))

                # Experience text
                exp_texts = [f"{e.role} at {e.company}: {e.responsibilities or ''}" for e in c.experience]
                texts_pool.append(" ".join(exp_texts))
                pool_keys.append((c.id, "exp"))

                # Projects text
                proj_texts = [f"{p.project_name}: {p.description or ''} {', '.join(p.technologies_used)}" for p in c.projects]
                texts_pool.append(" ".join(proj_texts))
                pool_keys.append((c.id, "proj"))

                # Education text
                edu_texts = [f"{e.degree} from {e.university or e.college or ''}" for e in c.education]
                texts_pool.append(" ".join(edu_texts))
                pool_keys.append((c.id, "edu"))

            logger.info(f"Generating {len(texts_pool)} segment embeddings in batch")
            embeddings_results = generator.generate_embeddings_batch(texts_pool)

            # Unpack results
            for (c_id, text_type), vec in zip(pool_keys, embeddings_results, strict=False):
                if text_type == "raw":
                    cand_embs[c_id] = vec
                elif text_type == "exp":
                    exp_embs[c_id] = vec
                elif text_type == "proj":
                    proj_embs[c_id] = vec
                elif text_type == "edu":
                    edu_embs[c_id] = vec

        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            errors.append(f"Embeddings Error: {str(e)}")

    duration = time.perf_counter() - start_time
    timing = dict(state.get("timing") or {})
    timing["generate_embeddings"] = duration

    return {
        **state,
        "jd_embedding": jd_embedding,
        "candidate_embeddings": cand_embs,
        "candidate_experience_embeddings": exp_embs,
        "candidate_project_embeddings": proj_embs,
        "candidate_education_embeddings": edu_embs,
        "errors": errors,
        "timing": timing
    }


# 5. Semantic Similarity Node
def similarity_calculation_node(state: AgentState) -> AgentState:
    """Calculates vector cosine similarity between elements."""
    start_time = time.perf_counter()
    scores = dict(state.get("scores") or {})

    jd_emb = state.get("jd_embedding")
    candidates = state.get("candidates") or []

    if jd_emb and candidates:
        for c in candidates:
            c_emb = state.get("candidate_embeddings", {}).get(c.id)
            exp_emb = state.get("candidate_experience_embeddings", {}).get(c.id)
            proj_emb = state.get("candidate_project_embeddings", {}).get(c.id)
            edu_emb = state.get("candidate_education_embeddings", {}).get(c.id)

            raw_cosine = compute_cosine_similarity(c_emb, jd_emb) if c_emb else 0.0
            exp_cosine = compute_cosine_similarity(exp_emb, jd_emb) if exp_emb else 0.0
            proj_cosine = compute_cosine_similarity(proj_emb, jd_emb) if proj_emb else 0.0
            edu_cosine = compute_cosine_similarity(edu_emb, jd_emb) if edu_emb else 0.0

            scores[c.id] = Score(
                overall_score=0.0,
                breakdown=ScoreBreakdown(
                    skill_match=0.0,
                    keyword_match=0.0,
                    experience_match=exp_cosine,
                    project_match=proj_cosine,
                    education_match=edu_cosine,
                    certification_match=0.0,
                    semantic_similarity=raw_cosine
                )
            )

    duration = time.perf_counter() - start_time
    timing = dict(state.get("timing") or {})
    timing["semantic_similarity"] = duration

    return {
        **state,
        "scores": scores,
        "timing": timing
    }


# 6. Rule-Based Scoring Node
def rule_based_scoring_node(state: AgentState) -> AgentState:
    """Computes overall weighted match scores."""
    start_time = time.perf_counter()
    scores = dict(state.get("scores") or {})
    candidates = state.get("candidates") or []
    jd = state.get("job_description")

    if jd and candidates:
        generator = SentenceTransformerGenerator()
        scorer = CandidateScorer(generator)

        for c in candidates:
            # Overwrite scores with fully evaluated score breakdown
            scores[c.id] = scorer.calculate_score(c, jd)

    duration = time.perf_counter() - start_time
    timing = dict(state.get("timing") or {})
    timing["rule_based_scoring"] = duration

    return {
        **state,
        "scores": scores,
        "timing": timing
    }


# 7. LLM Analysis Node
async def llm_analysis_node(state: AgentState) -> AgentState:
    """Queries model providers to analyze strengths, weaknesses, and personalized questions."""
    start_time = time.perf_counter()
    errors = []

    candidates = state.get("candidates") or []
    jd = state.get("job_description")
    llm_analysis_map = dict(state.get("llm_analysis") or {})
    recommendations = dict(state.get("recommendations") or {})

    if jd and candidates:
        try:
            llm = get_llm_client()
            structured_llm = llm.with_structured_output(LLMAnalysisResult)

            # Asynchronously query LLM for all candidates in parallel
            async def run_llm_for_candidate(cand: Candidate) -> None:
                try:
                    summary_text = (
                        f"Name: {cand.full_name}\n"
                        f"Skills Extracted: {', '.join(cand.skills)}\n"
                        f"Summary: {cand.summary or ''}\n"
                        f"Experience (Years): {cand.total_experience_years}\n"
                    )
                    prompt = PromptLoader.get_prompt(
                        "candidate_analysis",
                        job_description=jd.raw_content,
                        candidate_profile=summary_text
                    )

                    if hasattr(structured_llm, "ainvoke"):
                        res = await structured_llm.ainvoke(prompt)
                    else:
                        res = structured_llm.invoke(prompt)

                    from typing import cast
                    res_typed = cast(LLMAnalysisResult, res)

                    llm_analysis_map[cand.id] = {
                        "strengths": res_typed.strengths,
                        "weaknesses": res_typed.weaknesses,
                        "missing_skills": res_typed.missing_skills,
                        "interview_questions": res_typed.interview_questions,
                        "learning_recommendations": res_typed.learning_recommendations,
                        "hiring_summary": res_typed.hiring_summary,
                        "recommendation": res_typed.recommendation
                    }
                    recommendations[cand.id] = res_typed.recommendation
                except Exception as ex:
                    logger.error(f"Structured LLM failed for {cand.full_name}: {str(ex)}")
                    errors.append(f"LLM Analysis Error '{cand.full_name}': {str(ex)}")

            tasks = [run_llm_for_candidate(c) for c in candidates]
            await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(f"Structured LLM Analysis failed: {str(e)}")
            errors.append(f"LLM Analysis Error: {str(e)}")

    duration = time.perf_counter() - start_time
    timing = dict(state.get("timing") or {})
    timing["llm_analysis"] = duration

    return {
        **state,
        "llm_analysis": llm_analysis_map,
        "recommendations": recommendations,
        "errors": errors,
        "timing": timing
    }


# 8. Candidate Recommendation Node
def candidate_recommendation_node(state: AgentState) -> AgentState:
    """Enforces hiring decision rule designations based on score ranges."""
    start_time = time.perf_counter()
    recommendations = dict(state.get("recommendations") or {})
    scores = state.get("scores") or {}

    for cand_id, score in scores.items():
        score_val = score.overall_score

        # Decision mapping rules
        if score_val >= 90.0:
            rec = "Strong Hire"
        elif score_val >= 80.0:
            rec = "Hire"
        elif score_val >= 70.0:
            rec = "Consider"
        elif score_val >= 60.0:
            rec = "Review"
        else:
            rec = "Reject"

        recommendations[cand_id] = rec

    duration = time.perf_counter() - start_time
    timing = dict(state.get("timing") or {})
    timing["candidate_recommendation"] = duration

    return {
        **state,
        "recommendations": recommendations,
        "timing": timing
    }


# 9. Ranking Node
def ranking_node(state: AgentState) -> AgentState:
    """Sorts candidates deterministically by multi-attribute scoring weights."""
    start_time = time.perf_counter()
    candidates = state.get("candidates") or []
    scores = state.get("scores") or {}

    evaluations = []
    for c in candidates:
        sc = scores.get(c.id)
        if sc:
            evaluations.append((c, sc))

    # Deterministic sorting key
    def deterministic_key(item: tuple[Candidate, Score]) -> tuple[float, float, float, float, str]:
        cand, score = item
        return (
            -score.overall_score,
            -score.breakdown.semantic_similarity,
            -cand.total_experience_years,
            -score.confidence_score,
            cand.full_name or ""
        )

    sorted_evals = sorted(evaluations, key=deterministic_key)

    rankings = []
    for idx, (cand, score) in enumerate(sorted_evals):
        rankings.append(Ranking(
            candidate_id=cand.id,
            candidate_name=cand.full_name or "Candidate Name",
            rank=idx + 1,
            score=score
        ))

    duration = time.perf_counter() - start_time
    timing = dict(state.get("timing") or {})
    timing["ranking"] = duration

    return {
        **state,
        "rankings": rankings,
        "timing": timing
    }


# 10. Report Generation Node
def report_generation_node(state: AgentState) -> AgentState:
    """Compiles the final Report object including timings and statistics."""
    start_time = time.perf_counter()
    jd = state.get("job_description")
    rankings = state.get("rankings") or []

    report = None
    if jd:
        report = Report(
            job_description_id=jd.id,
            job_title=jd.title,
            rankings=rankings,
            evaluation_timestamp=datetime.utcnow(),
            exported_files={}
        )

    duration = time.perf_counter() - start_time
    timing = dict(state.get("timing") or {})
    timing["report_generation"] = duration

    # Save overall execution metadata stats
    metadata = dict(state.get("metadata") or {})
    metadata["processed_count"] = len(rankings)
    metadata["model"] = settings.MODEL_NAME
    metadata["embeddings_model"] = settings.EMBEDDING_MODEL

    return {
        **state,
        "report": report,
        "metadata": metadata,
        "timing": timing
    }


# Setup workflow StateGraph
workflow = StateGraph(AgentState)

# Register nodes
workflow.add_node("validate_input", validate_input_node)
workflow.add_node("parse_jd", parse_jd_node)
workflow.add_node("load_resumes", load_resumes_node)
workflow.add_node("embedding_generation", embedding_generation_node)
workflow.add_node("similarity_calculation", similarity_calculation_node)
workflow.add_node("score_generation", rule_based_scoring_node)
workflow.add_node("reasoning_generation", llm_analysis_node)
workflow.add_node("recommendation", candidate_recommendation_node)
workflow.add_node("ranking", ranking_node)
workflow.add_node("report_generation", report_generation_node)

# Set entry point
workflow.set_entry_point("validate_input")

# Connect conditional validation logic
workflow.add_conditional_edges(
    "validate_input",
    should_continue,
    {
        "continue": "parse_jd",
        "end": END
    }
)

# Connect remaining sequential states
workflow.add_edge("parse_jd", "load_resumes")
workflow.add_edge("load_resumes", "embedding_generation")
workflow.add_edge("embedding_generation", "similarity_calculation")
workflow.add_edge("similarity_calculation", "score_generation")
workflow.add_edge("score_generation", "reasoning_generation")
workflow.add_edge("reasoning_generation", "recommendation")
workflow.add_edge("recommendation", "ranking")
workflow.add_edge("ranking", "report_generation")
workflow.add_edge("report_generation", END)

# Compile graph
app_graph = workflow.compile()
