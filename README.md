# Smart Project Data Extractor & RAG Assistant

## Overview

The Smart Project Data Extractor & RAG Assistant helps consulting, infrastructure, and energy teams turn long project PDFs into useful answers and structured information. It combines document search with AI-assisted extraction so teams can spend less time reading lengthy technical and ESG reports and more time reviewing findings, comparing projects, and making decisions.

Upload project documents to ask context-aware questions or extract a consistent set of project fields for analysis. The application is built as a lightweight Streamlit tool that can run locally or be deployed on an organization-managed host.

## Key Features

### Interactive RAG Chat

- Ask questions about uploaded PDFs, including reports of 50 or more pages.
- Retrieves relevant text passages from the indexed documents and uses them as the answer context.
- Grounds responses in the uploaded document context and reports when the retrieved material does not contain an answer.
- Displays source document names and page references where available.

### Automated Data Extractor

- Extracts project information into a defined Pydantic `ProjectData` schema.
- Produces structured JSON with fields for client company, methodology, prototype count, target persona, and project outcome.
- Displays the result as JSON and a table, then exports it as `extracted_project_data.csv` using Pandas.

### Local File Management

- Saves uploaded PDFs to the local `uploads/` directory and scans that directory when the app starts.
- Lists saved PDFs in the sidebar, where individual files can be deleted.
- Builds a ChromaDB vector store and keeps it in Streamlit session state to avoid re-indexing on every interaction. The index can be rebuilt from the locally saved PDFs when needed.
- Keeps `.env` credentials and uploaded PDFs out of Git through `.gitignore`.

## Tech Stack

- **Python** — application language
- **Streamlit** — user interface and session state
- **LangChain** — document splitting, retrieval, and model orchestration
- **OpenAI API** — chat model and text embeddings
- **Pydantic** — structured extraction schema and validation
- **ChromaDB** — vector store for document chunks
- **Pandas** — tabular display and CSV export
- **pdfplumber** — PDF text extraction
- **python-dotenv** — local environment variable loading

## Project Structure

```text
.
├── app.py                 # Streamlit entry point and user interface
├── document_manager.py    # Local PDF storage, text extraction, and chunking
├── rag_engine.py          # OpenAI embeddings, ChromaDB, and RAG answers
├── extractor.py           # Pydantic schema and structured data extraction
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
├── .env                   # Local API key; create this file yourself
└── uploads/               # Created automatically for uploaded PDFs
```

## Installation & Setup

### 1. Get the repository

Clone the repository using its remote URL, replacing the example owner and repository with the correct values:

```bash
git clone https://github.com/OWNER/REPOSITORY.git
cd Smart-Project-Data-Extractor-RAG-Assistant
```

Alternatively, download the repository as a ZIP file and extract it. Open a terminal in the project directory before continuing.

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

Activate it in PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Or activate it on macOS/Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the OpenAI API key

Create a file named `.env` in the project root and add your API key:

```dotenv
OPENAI_API_KEY="sk-..."
```

Replace the placeholder with a valid key. The application loads it locally through `python-dotenv`. Do not commit the `.env` file to source control.

## Usage

Start the application from the project directory with the virtual environment activated:

```bash
streamlit run app.py
```

Then use the sidebar to choose a module and manage documents:

1. **Upload PDFs:** Add one or more PDF reports in the sidebar. The app saves them under `uploads/`, extracts their text, and builds the retrieval index when an API key is configured.
2. **RAG Chat:** Ask questions about the saved reports. Review the answer and its cited source documents and page numbers.
3. **Auto-Extractor:** Select **Analyze and Structure** to extract the defined project fields. Review the JSON and table, then download the CSV.
4. **Manage files:** Use the ❌ control beside a listed PDF to remove that file. The index is rebuilt from the remaining saved PDFs.

The extractor currently sends up to 40,000 characters of combined PDF text to the model. Results should be reviewed before they are used in formal reporting or decision-making.

## Data Handling Notes

PDFs are stored on the machine or server running the application. The ChromaDB index is held in Streamlit session state and can be recreated from those PDFs; it is not configured as a persistent on-disk vector database. Extracted PDF text is sent to the OpenAI API for embedding and model requests. Before processing sensitive project material, follow your organization's data governance and AI usage requirements.

Text extraction depends on selectable text in the PDF. Scanned image-only documents may require OCR, which is not included in this project.
