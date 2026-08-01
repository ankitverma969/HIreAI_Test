"""Shared pytest fixtures and configuration for the HIreAI test suite."""

import pytest


@pytest.fixture(autouse=True)
def _reset_global_stores():
    """Reset in-memory stores before every test to ensure test isolation."""
    from app.api.router import (
        CANDIDATE_STORE,
        GLOBAL_STATE,
        LLM_ANALYSIS_STORE,
        RESULTS_STORE,
    )

    CANDIDATE_STORE.clear()
    RESULTS_STORE.clear()
    LLM_ANALYSIS_STORE.clear()
    GLOBAL_STATE["last_report_id"] = None

    yield

    # Cleanup after test as well
    CANDIDATE_STORE.clear()
    RESULTS_STORE.clear()
    LLM_ANALYSIS_STORE.clear()
    GLOBAL_STATE["last_report_id"] = None
