import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel

from app.core.config import settings
from app.exporters.report_exporter import ReportExporter
from app.graph.workflow import app_graph
from app.models.candidate import Candidate
from app.models.report import Report
from app.models.response import SuccessResponse

router = APIRouter()

# In-memory session store (no database, as per requirements)
RESULTS_STORE: dict[str, Report] = {}
CANDIDATE_STORE: dict[str, Candidate] = {}
LLM_ANALYSIS_STORE: dict[str, dict[str, Any]] = {}
GLOBAL_STATE: dict[str, Any] = {
    "last_report_id": None
}

class ScreenPayload(BaseModel):
    job_description_path: str
    resumes_paths: list[str]


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {str(e)}")
                self.disconnect(connection)

manager = ConnectionManager()


@router.get("/", response_model=SuccessResponse[dict[str, str]])
async def root() -> SuccessResponse[dict[str, str]]:
    """Root endpoint welcoming users to the screening service."""
    return SuccessResponse(
        message=f"Welcome to the {settings.APP_NAME} Service",
        data={"status": "online", "documentation": "/docs"},
    )


@router.get("/health", response_model=SuccessResponse[dict[str, str]])
async def health() -> SuccessResponse[dict[str, str]]:
    """Health check endpoint checking application viability."""
    return SuccessResponse(
        message="System status healthy",
        data={"status": "healthy", "timestamp": datetime.utcnow().isoformat()},
    )


@router.get("/version", response_model=SuccessResponse[dict[str, str]])
async def version() -> SuccessResponse[dict[str, str]]:
    """Version check endpoint returning current release metadata."""
    return SuccessResponse(
        message="Version check succeeded",
        data={"app_name": settings.APP_NAME, "version": settings.APP_VERSION},
    )


# WebSocket endpoint for progress updates
@router.websocket("/ws")
async def websocket_progress(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        # Keep connection open and handle client pings
        while True:
            await websocket.receive_text()
            # Echo back ping to confirm connection is healthy
            await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)


# Upload Job Description
@router.post("/job-description/upload")
async def upload_job_description(file: UploadFile = File(...)) -> SuccessResponse[dict[str, Any]]:  # noqa: B008
    """Saves uploaded Job Description file to temporary uploads folder."""
    try:
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Keep original extension
        ext = Path(file.filename or "jd.txt").suffix or ".txt"
        file_path = upload_dir / f"jd_{int(time.time())}{ext}"

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Job Description uploaded successfully: {file_path}")
        return SuccessResponse(
            message="Job description uploaded successfully.",
            data={
                "filename": file.filename,
                "saved_path": str(file_path.absolute()),
                "size_bytes": len(content)
            }
        )
    except Exception as e:
        logger.error(f"Failed to upload Job Description: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload JD: {str(e)}"
        ) from e


# Upload Multiple Resumes
@router.post("/resumes/upload")
async def upload_resumes(files: list[UploadFile] = File(...)) -> SuccessResponse[list[dict[str, Any]]]:  # noqa: B008
    """Saves multiple resume uploads to temporary folders."""
    try:
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        uploaded_details = []
        for file in files:
            Path(file.filename or "resume.pdf").suffix or ".pdf"
            file_path = upload_dir / f"resume_{int(time.time())}_{file.filename}"

            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            uploaded_details.append({
                "filename": file.filename,
                "saved_path": str(file_path.absolute()),
                "size_bytes": len(content)
            })

        logger.info(f"Uploaded {len(uploaded_details)} resumes successfully.")
        return SuccessResponse(
            message="Resumes uploaded successfully.",
            data=uploaded_details
        )
    except Exception as e:
        logger.error(f"Failed to upload resumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload resumes: {str(e)}"
        ) from e


# Screen Resumes endpoint with WebSockets updates
@router.post("/screen")
async def screen_resumes(payload: ScreenPayload) -> SuccessResponse[dict[str, Any]]:
    """Runs the LangGraph candidate screening workflow, streaming node execution via WebSocket."""
    logger.info(f"Initiating screening pipeline for JD: {payload.job_description_path} with {len(payload.resumes_paths)} candidates.")

    from app.graph import AgentState
    initial_state: AgentState = {
        "job_description_path": payload.job_description_path,
        "resumes_paths": payload.resumes_paths,
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

    # Broadcast start screening event
    await manager.broadcast({
        "type": "progress",
        "stage": "validate_input",
        "status": "in_progress",
        "message": "Initiating candidate screening pipeline validation checks..."
    })

    try:
        final_state: AgentState = initial_state

        # Execute the StateGraph using .astream to send live node execution progress updates!
        async for chunk in app_graph.astream(initial_state, stream_mode="updates"):
            # chunk contains mapping from node_name -> state update
            node_name = list(chunk.keys())[0]
            logger.info(f"LangGraph node completed: {node_name}")

            # Map node names to UI descriptive stages
            stage_messages = {
                "validate_input": "Inputs validated. File structure matches requirements.",
                "parse_jd": "Job Description document parsed and structured.",
                "load_resumes": "Candidate resume documents parsed and extracted.",
                "embedding_generation": "Generating sentence-transformers dense vector embeddings...",
                "similarity_calculation": "Calculating cosine similarity index score maps...",
                "score_generation": "Applying rule-based scoring engines and weights...",
                "reasoning_generation": "Generating AI Recruiter strengths, weaknesses, and interview questions...",
                "recommendation": "Aggregating candidate final decision suggestions...",
                "ranking": "Sorting candidates deterministically based on match values...",
                "report_generation": "Compiling final ATS reports and statistics."
            }

            msg = stage_messages.get(node_name, f"Processed phase {node_name} successfully.")

            # Broadcast update
            await manager.broadcast({
                "type": "progress",
                "stage": node_name,
                "status": "completed",
                "message": msg
            })

            # Aggregate final state chunks
            for key, val in chunk[node_name].items():
                final_state[key] = val  # type: ignore [literal-required]

        # Retrieve report
        report = final_state.get("report")
        if not report:
            error_msgs = "; ".join(final_state.get("errors") or ["Unknown workflow termination."])
            raise ValueError(f"Screening workflow terminated without report: {error_msgs}")

        assert isinstance(report, Report)

        # Store report & candidates in memory cache
        report_id = report.job_description_id or f"REP_{int(time.time())}"
        RESULTS_STORE[report_id] = report
        GLOBAL_STATE["last_report_id"] = report_id

        candidates_list = final_state.get("candidates") or []
        assert isinstance(candidates_list, list)

        for cand in candidates_list:
            assert isinstance(cand, Candidate)
            CANDIDATE_STORE[cand.id] = cand

        # Store structured LLM qualitative analysis details
        for cand_id, val in final_state.get("llm_analysis", {}).items():
            LLM_ANALYSIS_STORE[cand_id] = val

        # Broadcast completed status
        await manager.broadcast({
            "type": "completed",
            "stage": "completed",
            "status": "success",
            "message": "Screening completed successfully!",
            "report_id": report_id
        })

        return SuccessResponse(
            message="Resume screening completed successfully.",
            data={
                "report_id": report_id,
                "candidates_count": len(report.rankings),
                "job_title": report.job_title
            }
        )
    except Exception as e:
        logger.error(f"Screening pipeline error: {str(e)}")
        await manager.broadcast({
            "type": "error",
            "stage": "failed",
            "status": "error",
            "message": f"Screening failed: {str(e)}"
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Screening workflow failed: {str(e)}"
        ) from e


# Retrieve current screening results
@router.get("/results")
async def get_results() -> SuccessResponse[dict[str, Any]]:
    """Retrieves the rankings and score breakdowns from the latest screening report."""
    report_id = GLOBAL_STATE.get("last_report_id")
    if not report_id or report_id not in RESULTS_STORE:
        return SuccessResponse(
            message="No screening results found.",
            data={"rankings": [], "job_title": None, "report_id": None}
        )

    report = RESULTS_STORE[report_id]
    return SuccessResponse(
        message="Rankings and screening results retrieved.",
        data={
            "report_id": report_id,
            "job_title": report.job_title,
            "evaluation_timestamp": report.evaluation_timestamp.isoformat(),
            "rankings": [r.model_dump() for r in report.rankings]
        }
    )


# Retrieve single candidate profile
@router.get("/candidate/{candidate_id}")
async def get_candidate_details(candidate_id: str) -> SuccessResponse[dict[str, Any]]:
    """Retrieves candidate structured profile matching ID."""
    if candidate_id not in CANDIDATE_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID '{candidate_id}' not found."
        )

    candidate = CANDIDATE_STORE[candidate_id]

    # Retrieve score matching candidate from last report
    report_id = GLOBAL_STATE.get("last_report_id")
    score_details = None
    if report_id and report_id in RESULTS_STORE:
        report = RESULTS_STORE[report_id]
        for ranking in report.rankings:
            if ranking.candidate_id == candidate_id:
                score_details = ranking.score.model_dump()
                break

    return SuccessResponse(
        message="Candidate details retrieved.",
        data={
            "profile": candidate.model_dump(),
            "score": score_details,
            "analysis": LLM_ANALYSIS_STORE.get(candidate_id)
        }
    )


# Download files
@router.get("/download/csv")
async def download_csv() -> FileResponse:
    """Generates and downloads CSV format report."""
    report_id = GLOBAL_STATE.get("last_report_id")
    if not report_id or report_id not in RESULTS_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No screening reports found to export."
        )

    report = RESULTS_STORE[report_id]
    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "screening_report.csv"

    exporter = ReportExporter()
    exporter.export_csv(report, str(out_path))

    return FileResponse(
        path=out_path,
        filename="resume_screening_report.csv",
        media_type="text/csv"
    )


@router.get("/download/json")
async def download_json() -> FileResponse:
    """Generates and downloads JSON format report."""
    report_id = GLOBAL_STATE.get("last_report_id")
    if not report_id or report_id not in RESULTS_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No screening reports found to export."
        )

    report = RESULTS_STORE[report_id]
    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "screening_report.json"

    exporter = ReportExporter()
    exporter.export_json(report, str(out_path))

    return FileResponse(
        path=out_path,
        filename="resume_screening_report.json",
        media_type="application/json"
    )


@router.get("/download/report")
async def download_report() -> FileResponse:
    """Generates and downloads Markdown format report."""
    report_id = GLOBAL_STATE.get("last_report_id")
    if not report_id or report_id not in RESULTS_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No screening reports found to export."
        )

    report = RESULTS_STORE[report_id]
    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "screening_report.md"

    exporter = ReportExporter()
    exporter.export_markdown_report(report, str(out_path))

    return FileResponse(
        path=out_path,
        filename="resume_screening_report.md",
        media_type="text/markdown"
    )
