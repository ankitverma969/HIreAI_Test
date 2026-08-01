def test_backend_imports() -> None:
    """Verifies that all backend components can be imported without errors."""
    from app.core.config import settings
    from app.core.logging import setup_logging
    from app.core.constants import BASE_DIR
    from app.core.security import validate_api_key
    from app.core.exceptions import ResumeAgentException
    
    from app.models.candidate import Candidate
    from app.models.job_description import JobDescription
    from app.models.score import Score
    from app.models.report import Report
    from app.models.response import SuccessResponse
    
    from app.api.router import router
    from app.api.dependencies import get_settings
    
    from app.graph.state import AgentState
    from app.graph.workflow import app_graph
    
    from app.parser.interface import BaseResumeParser
    from app.extractor.interface import BaseCandidateExtractor
    from app.scorer.interface import BaseCandidateScorer
    from app.embeddings.interface import BaseEmbeddingGenerator
    from app.llm.client import BaseLLMClient
    from app.prompts.loader import PromptLoader
    from app.exporters.interface import BaseReportExporter
    from app.repositories.base import BaseRepository
    from app.services.agent_service import BaseAgentService
    from app.utils.helpers import is_supported_file

    assert settings.APP_NAME == "Resume Screening Agent"
    assert app_graph is not None
