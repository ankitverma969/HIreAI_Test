from datetime import datetime

import pandas as pd
import streamlit as st

# Page configuration for premium layout look
st.set_page_config(
    page_title="AI Resume Screening Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom premium styling injects (glassmorphic dark UI)
st.markdown(
    """
    <style>
    /* Dark themes and customized gradients */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f1f5f9;
    }
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 2.75rem;
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #6366f1;
    }
    .css-1542fc6 {
        background-color: #1e293b;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title Header
st.markdown(
    '<div class="main-title">AI Resume Screening Agent</div>', unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">Enterprise candidate match evaluator & qualitative rankings</div>',
    unsafe_allow_html=True,
)

# Sidebar Configuration
st.sidebar.image("https://img.icons8.com/isometric/512/bot.png", width=80)
st.sidebar.markdown("### Settings & Credentials")

# Inputs for settings
openai_key = st.sidebar.text_input(
    "OpenAI API Key", type="password", placeholder="sk-..."
)
groq_key = st.sidebar.text_input("Groq API Key", type="password", placeholder="gsk-...")

model_option = st.sidebar.selectbox(
    "LLM Architecture Model",
    ["gpt-4o-mini", "gpt-4o", "llama-3-70b-groq", "mixtral-8x7b-groq"],
)

embedding_option = st.sidebar.selectbox(
    "Embedding Transformer Model", ["all-MiniLM-L6-v2", "text-embedding-3-small"]
)

log_level = st.sidebar.select_slider(
    "System Logging Output Verbosity",
    options=["DEBUG", "INFO", "WARNING", "ERROR"],
    value="INFO",
)

st.sidebar.divider()
st.sidebar.markdown("### Workspace Metrics (Mock)")
col1, col2 = st.sidebar.columns(2)
col1.metric("Processed JDs", "0")
col2.metric("Screened Resumes", "0")

# Main Content Layout: Multi-tab layout
tab1, tab2, tab3 = st.tabs(
    ["📋 Upload & Settings", "📊 Match Analysis", "📂 Export & Reports"]
)

with tab1:
    st.subheader("1. Upload Target Job Description")
    jd_file = st.file_uploader(
        "Upload Job Description (TXT or PDF)", type=["txt", "pdf"], key="jd_uploader"
    )

    st.subheader("2. Upload Candidate Resumes")
    resume_files = st.file_uploader(
        "Select candidate resumes (PDF, DOCX, or TXT)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="resumes_uploader",
    )

    if st.button("Start AI Screening Workflow", type="primary"):
        if not jd_file:
            st.warning("Please upload a Job Description before proceeding.")
        elif not resume_files:
            st.warning("Please upload at least one candidate resume.")
        else:
            st.info(
                "Screening process triggered. Graph workflow skeleton will execute when business logic is implemented."
            )

with tab2:
    st.subheader("Scoring Rankings Overview")
    st.info("Upload materials in tab 1 to calculate scores.")

    # Mock data layout to visualize end target
    mock_data = {
        "Rank": [1, 2],
        "Candidate Name": ["John Doe (Sample)", "Jane Smith (Sample)"],
        "Overall Match": ["92.5%", "78.0%"],
        "Skills Score": ["95.0%", "80.0%"],
        "Experience Score": ["90.0%", "75.0%"],
    }
    st.table(pd.DataFrame(mock_data))

with tab3:
    st.subheader("Reports Generator & Outbox")
    st.write(
        "Extract analysis logs, candidate list indices, and summaries in format of choice."
    )

    csv_col, json_col, md_col = st.columns(3)
    csv_col.button("Download CSV Dataset", disabled=True)
    json_col.button("Download JSON Schema", disabled=True)
    md_col.button("Download Text Summary", disabled=True)

# Centralized status message dashboard
st.divider()
st.caption(
    f"System Running Framework: FastAPI Backend / Streamlit UI • Version 1.0.0 • Local Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
