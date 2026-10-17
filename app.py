import hashlib
import os
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from document_manager import DocumentManager
from extractor import DataExtractor
from rag_engine import RAGEngine


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=PROJECT_DIR / ".env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

st.set_page_config(
    page_title="Smart Project Data Extractor",
    layout="wide",
)

st.markdown(
    """
    <style>
        .app-title {
            text-align: center;
            font-size: 2.25rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin: 0.25rem 0 0.35rem;
        }
        .app-subtitle {
            text-align: center;
            color: #667085;
            font-size: 1.05rem;
            margin: 0 auto 2rem;
        }
        .app-section-title {
            text-align: center;
            font-size: 1.65rem;
            font-weight: 650;
            margin: 0.5rem 0 1.5rem;
        }
        .st-key-nav_rag_chat button,
        .st-key-nav_auto_extractor button {
            min-height: 2.7rem;
            border-radius: 0.65rem;
            font-weight: 600;
            transition: background-color 120ms ease, border-color 120ms ease;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_api_key_fingerprint(api_key):
    """Return a non-reversible identifier for the configured API key."""
    if not api_key:
        return None
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


if "document_manager" not in st.session_state:
    st.session_state.document_manager = DocumentManager(
        upload_dir=PROJECT_DIR / "uploads"
    )
if "messages" not in st.session_state:
    st.session_state.messages = []
if "indexed_document_signature" not in st.session_state:
    st.session_state.indexed_document_signature = None
if "failed_index_signature" not in st.session_state:
    st.session_state.failed_index_signature = None
if "indexing_error" not in st.session_state:
    st.session_state.indexing_error = None
if "extraction_result" not in st.session_state:
    st.session_state.extraction_result = None
if "extraction_signature" not in st.session_state:
    st.session_state.extraction_signature = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())
if "current_page" not in st.session_state:
    st.session_state.current_page = "RAG Chat"

api_key_fingerprint = get_api_key_fingerprint(OPENAI_API_KEY)
if (
    "api_key_fingerprint" not in st.session_state
    or st.session_state.api_key_fingerprint != api_key_fingerprint
    or "rag_engine" not in st.session_state
    or "data_extractor" not in st.session_state
):
    st.session_state.api_key_fingerprint = api_key_fingerprint
    st.session_state.rag_engine = (
        RAGEngine(OPENAI_API_KEY) if OPENAI_API_KEY else None
    )
    st.session_state.data_extractor = (
        DataExtractor(OPENAI_API_KEY) if OPENAI_API_KEY else None
    )
    st.session_state.indexed_document_signature = None
    st.session_state.failed_index_signature = None
    st.session_state.indexing_error = None
    st.session_state.messages = []


st.sidebar.subheader("Navigation")
if st.sidebar.button(
    "RAG Chat",
    key="nav_rag_chat",
    use_container_width=True,
):
    st.session_state.current_page = "RAG Chat"
if st.sidebar.button(
    "Auto-Extractor",
    key="nav_auto_extractor",
    use_container_width=True,
):
    st.session_state.current_page = "Auto-Extractor"

active_nav_key = (
    "nav_rag_chat"
    if st.session_state.current_page == "RAG Chat"
    else "nav_auto_extractor"
)
st.markdown(
    f"""
    <style>
        .st-key-{active_nav_key} button {{
            background-color: #344054 !important;
            border-color: #344054 !important;
            color: #ffffff !important;
        }}
        .st-key-{active_nav_key} button:hover {{
            background-color: #1d2939 !important;
            border-color: #1d2939 !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Document setup")
    uploaded_files = st.file_uploader(
        "Upload PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
        key=st.session_state.uploader_key,
    )

document_manager = st.session_state.document_manager

upload_error = None
if uploaded_files:
    try:
        for uploaded_file in uploaded_files:
            document_manager.save_uploaded_file(uploaded_file)
    except Exception as error:
        upload_error = str(error)
        st.sidebar.error(f"Could not save one or more uploaded PDFs: {upload_error}")
    else:
        rag_engine = st.session_state.get("rag_engine")
        if rag_engine is not None:
            rag_engine.clear_index()

        st.session_state.pop("rag_engine", None)
        st.session_state.uploader_key = str(uuid.uuid4())
        st.session_state.indexed_document_signature = None
        st.session_state.failed_index_signature = None
        st.session_state.indexing_error = None
        st.session_state.messages = []
        st.session_state.extraction_result = None
        st.session_state.extraction_signature = None
        st.rerun()

saved_files = document_manager.list_saved_pdfs()
current_document_signature = (
    document_manager.get_signature(saved_files) if saved_files else None
)

if saved_files:
    st.sidebar.markdown("**Loaded local PDF files**")
    for file_path in saved_files:
        col1, col2 = st.sidebar.columns([4, 1], vertical_alignment="center")
        display_name = document_manager.get_display_name(file_path)
        with col1:
            st.write(display_name)
        with col2:
            if st.button(
                "\u274c",
                key=f"delete_{file_path.name}",
                help=f"Delete {display_name}",
            ):
                try:
                    os.remove(file_path)
                    rag_engine = st.session_state.get("rag_engine")
                    if rag_engine is not None:
                        rag_engine.clear_index()

                    st.session_state.indexed_document_signature = None
                    st.session_state.failed_index_signature = None
                    st.session_state.indexing_error = None
                    st.session_state.messages = []
                    st.session_state.extraction_result = None
                    st.session_state.extraction_signature = None
                    st.session_state.uploader_key = str(uuid.uuid4())
                    st.rerun()
                except OSError as error:
                    st.sidebar.error(
                        f"Could not delete {display_name}. ({type(error).__name__})"
                    )
else:
    st.sidebar.info("No PDF documents are currently saved in uploads/.")

if current_document_signature is None:
    rag_engine = st.session_state.get("rag_engine")
    if rag_engine is not None:
        rag_engine.clear_index()
    st.session_state.indexed_document_signature = None
    st.session_state.failed_index_signature = None
    st.session_state.indexing_error = None
    st.session_state.messages = []
elif OPENAI_API_KEY:
    rag_engine = st.session_state.rag_engine
    index_is_ready = (
        st.session_state.indexed_document_signature == current_document_signature
        and rag_engine is not None
        and rag_engine.retriever is not None
    )

    if index_is_ready:
        st.sidebar.success("Local PDFs are indexed and ready for chat.")
    else:
        retry_indexing = False
        if current_document_signature == st.session_state.failed_index_signature:
            st.sidebar.error(st.session_state.indexing_error)
            retry_indexing = st.sidebar.button(
                "Retry document indexing",
                key="retry_document_indexing",
            )
        else:
            retry_indexing = True

        if retry_indexing:
            rag_engine.clear_index()
            st.session_state.indexed_document_signature = None
            st.session_state.messages = []

            try:
                with st.spinner("Extracting PDF text and creating embeddings..."):
                    chunks = document_manager.process_pdfs(saved_files)
                    if not chunks:
                        raise ValueError(
                            "No extractable text was found. The PDFs may be scanned images."
                        )
                    rag_engine.index_documents(chunks)

                st.session_state.indexed_document_signature = (
                    current_document_signature
                )
                st.session_state.failed_index_signature = None
                st.session_state.indexing_error = None
                st.sidebar.success("Local PDFs are indexed and ready for chat.")
            except Exception as error:
                st.session_state.failed_index_signature = current_document_signature
                st.session_state.indexing_error = (
                    "Could not index the PDFs. Check the application configuration, file format, "
                    f"and connection, then retry. ({type(error).__name__})"
                )
                st.sidebar.error(st.session_state.indexing_error)

if st.session_state.extraction_signature != current_document_signature:
    st.session_state.extraction_result = None
    st.session_state.extraction_signature = current_document_signature

left_spacer, main_content, right_spacer = st.columns([1, 6, 1], gap="large")

with main_content:
    st.markdown(
        '<div class="app-title">Smart Project Data Extractor</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="app-subtitle">Ask questions about project documents or extract structured project data.</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.current_page == "RAG Chat":
        st.markdown(
            '<h2 class="app-section-title">Chat with your project documents</h2>',
            unsafe_allow_html=True,
        )
        messages_container = st.container()

        if not OPENAI_API_KEY:
            st.info("Document chat is currently unavailable.")
        elif not saved_files:
            st.info("Upload a PDF or place one in uploads/ to use document chat.")
        elif (
            st.session_state.indexed_document_signature != current_document_signature
            or st.session_state.rag_engine is None
            or st.session_state.rag_engine.retriever is None
        ):
            st.info("The PDFs are not ready yet. Check the indexing message in the sidebar.")
        else:
            with messages_container:
                for msg in st.session_state.messages:
                    st.chat_message(msg["role"]).markdown(msg["content"])

            prompt = st.chat_input("Ask a question...")
            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with messages_container:
                    st.chat_message("user").markdown(prompt)

                with messages_container:
                    with st.chat_message("assistant"):
                        with st.spinner("Searching the documents..."):
                            try:
                                answer, sources = st.session_state.rag_engine.answer_question(
                                    prompt
                                )
                                if sources:
                                    answer += "\n\n**Sources:** " + "; ".join(sources)
                            except Exception:
                                answer = (
                                    "I couldn't complete that request. Check the application "
                                    "configuration and connection, then try again."
                                )
                        st.markdown(answer)

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

    elif st.session_state.current_page == "Auto-Extractor":
        st.markdown(
            '<h2 class="app-section-title">Extract structured project data</h2>',
            unsafe_allow_html=True,
        )
        st.write("Analyze the saved PDFs and export the extracted project fields.")

        if st.button("Analyze and Structure", type="primary"):
            if upload_error:
                st.warning("Fix the upload issue in the sidebar before running the extractor.")
            elif not saved_files:
                st.warning("Upload a PDF or place one in uploads/ to get started.")
            elif not OPENAI_API_KEY:
                st.warning("The extractor is currently unavailable.")
            else:
                st.session_state.extraction_result = None
                try:
                    with st.spinner("Reading PDFs and extracting project data..."):
                        text_parts = []
                        for file_path in saved_files:
                            pdf_text = document_manager.extract_text(file_path)
                            if pdf_text.strip():
                                text_parts.append(
                                    f"Document: {document_manager.get_display_name(file_path)}\n"
                                    f"{pdf_text}"
                                )

                        combined_text = "\n\n---\n\n".join(text_parts).strip()
                        if not combined_text:
                            st.warning(
                                "No text could be extracted from the uploaded PDFs. "
                                "They may be scanned images."
                            )
                        else:
                            max_characters = DataExtractor.MAX_INPUT_CHARACTERS
                            if len(combined_text) > max_characters:
                                st.warning(
                                    "The combined PDF text is long. The extractor will "
                                    f"analyze the first {max_characters:,} characters."
                                )

                            dataframe = st.session_state.data_extractor.extract_data(
                                combined_text
                            )
                            st.session_state.extraction_result = dataframe.to_dict(
                                orient="records"
                            )[0]
                            st.session_state.extraction_signature = (
                                current_document_signature
                            )
                except Exception as error:
                    st.error(
                        "Project data extraction failed. Check the application configuration, PDF "
                        f"text, and connection. ({type(error).__name__})"
                    )

        if (
            st.session_state.extraction_result
            and st.session_state.extraction_signature == current_document_signature
        ):
            extracted_data = st.session_state.extraction_result
            dataframe = pd.DataFrame([extracted_data])

            st.markdown("### Extracted project data")
            st.json(extracted_data)
            st.table(dataframe)
            st.download_button(
                label="Download CSV",
                data=dataframe.to_csv(index=False).encode("utf-8"),
                file_name="extracted_project_data.csv",
                mime="text/csv",
            )
