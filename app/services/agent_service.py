from abc import ABC, abstractmethod

from loguru import logger

from app.core.exceptions import ResumeAgentException
from app.graph import AgentState, app_graph
from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.report import Report


class BaseAgentService(ABC):
    """Orchestrates job parsing, resume screening, scoring, ranking, and exporting."""

    @abstractmethod
    async def run_screening_workflow(
        self, job_description_path: str, resumes_paths: list[str]
    ) -> Report:
        """Triggers the full LangGraph-driven candidate screening workflow process."""
        pass


class AgentService(BaseAgentService):
    """Orchestrates job parsing, resume screening, scoring, ranking, and exporting via LangGraph."""

    async def run_screening_workflow(
        self,
        job_description_path: str,
        resumes_paths: list[str]
    ) -> Report:
        """Triggers the full LangGraph-driven candidate screening workflow process.

        Args:
            job_description_path: Path to the target Job Description file.
            resumes_paths: Paths to the target Candidate Resumes.

        Returns:
            The compiled Report details containing scores and ranks.

        Raises:
            ResumeAgentException: For any processing failure.
        """
        logger.info(f"Starting agent screening workflow. JD: '{job_description_path}', Resumes: {len(resumes_paths)}")

        initial_state: AgentState = {
            "job_description_path": job_description_path,
            "resumes_paths": resumes_paths,
            "job_description_raw": None,
            "candidates_input": [],
            "job_description": None,
            "candidates": [],
            "jd_embedding": None,
            "candidate_embeddings": {},
            "candidate_experience_embeddings": {},
            "candidate_project_embeddings": {},
            "candidate_education_embeddings": {},
            "scores": {},
            "llm_analysis": {},
            "recommendations": {},
            "rankings": [],
            "report": None,
            "metadata": {},
            "timing": {},
            "errors": [],
            "export_paths": {}
        }

        try:
            # Run LangGraph pipeline
            final_state = await app_graph.ainvoke(initial_state)

            # Check for critical workflow errors
            if final_state.get("errors") and not final_state.get("report"):
                error_msgs = "; ".join(final_state["errors"])
                logger.error(f"Workflow execution halted with errors: {error_msgs}")
                raise ResumeAgentException(f"Screening workflow failed: {error_msgs}")

            report = final_state.get("report")
            if not report:
                raise ResumeAgentException("Screening completed but failed to compile rankings or report.")

            logger.info("Screening workflow execution completed successfully.")
            assert isinstance(report, Report)
            return report

        except Exception as e:
            if isinstance(e, ResumeAgentException):
                raise e
            logger.critical(f"Unhandled exception in screening workflow: {str(e)}")
            raise ResumeAgentException(f"Screening workflow crashed: {str(e)}") from e

    async def run_screening_with_entities(
        self,
        job_description: JobDescription,
        candidates: list[Candidate]
    ) -> Report:
        """Helper execution endpoint passing pre-parsed memory objects directly.

        Args:
            job_description: Populated JobDescription model.
            candidates: List of Candidate models.

        Returns:
            Ranked Report model.

        Raises:
            ResumeAgentException: On pipeline error.
        """
        logger.info(f"Starting memory-direct screening. JD Title: '{job_description.title}', Candidates: {len(candidates)}")

        initial_state: AgentState = {
            "job_description_path": None,
            "resumes_paths": [],
            "job_description_raw": None,
            "candidates_input": candidates,
            "job_description": job_description,
            "candidates": candidates,
            "jd_embedding": None,
            "candidate_embeddings": {},
            "candidate_experience_embeddings": {},
            "candidate_project_embeddings": {},
            "candidate_education_embeddings": {},
            "scores": {},
            "llm_analysis": {},
            "recommendations": {},
            "rankings": [],
            "report": None,
            "metadata": {},
            "timing": {},
            "errors": [],
            "export_paths": {}
        }

        try:
            final_state = await app_graph.ainvoke(initial_state)

            if final_state.get("errors") and not final_state.get("report"):
                error_msgs = "; ".join(final_state["errors"])
                raise ResumeAgentException(f"Screening workflow failed: {error_msgs}")

            report = final_state.get("report")
            if not report:
                raise ResumeAgentException("Workflow completed but report is empty.")

            assert isinstance(report, Report)
            return report
        except Exception as e:
            if isinstance(e, ResumeAgentException):
                raise e
            raise ResumeAgentException(f"Direct screening workflow crashed: {str(e)}") from e
