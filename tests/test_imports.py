def test_backend_imports() -> None:
    """Verifies that all backend components can be imported without errors."""
    from app.core.config import settings
    from app.graph.workflow import app_graph

    assert settings.APP_NAME == "Resume Screening Agent"
    assert app_graph is not None
