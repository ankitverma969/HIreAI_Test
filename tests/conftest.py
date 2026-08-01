"""Shared pytest fixtures and configuration for the HIreAI test suite."""

import pytest


@pytest.fixture(autouse=True)
def _reset_global_stores():
    """Reset in-memory stores before every test to ensure test isolation."""
    from app.api.router import (
        CANDIDATE_STORE,
        CHAT_HISTORY_STORE,
        AUDIT_LOG_STORE,
        GLOBAL_STATE,
        GRAPH_TRACE_STORE,
        JOB_DESCRIPTION_STORE,
        LLM_ANALYSIS_STORE,
        PROMPT_HISTORY_STORE,
        RESULTS_STORE,
    )

    CANDIDATE_STORE.clear()
    RESULTS_STORE.clear()
    JOB_DESCRIPTION_STORE.clear()
    LLM_ANALYSIS_STORE.clear()
    CHAT_HISTORY_STORE.clear()
    GRAPH_TRACE_STORE.clear()
    AUDIT_LOG_STORE.clear()
    PROMPT_HISTORY_STORE.clear()
    GLOBAL_STATE["last_report_id"] = None

    yield

    # Cleanup after test as well
    CANDIDATE_STORE.clear()
    RESULTS_STORE.clear()
    JOB_DESCRIPTION_STORE.clear()
    LLM_ANALYSIS_STORE.clear()
    CHAT_HISTORY_STORE.clear()
    GRAPH_TRACE_STORE.clear()
    AUDIT_LOG_STORE.clear()
    PROMPT_HISTORY_STORE.clear()
    GLOBAL_STATE["last_report_id"] = None
