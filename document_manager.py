import hashlib
import re
from pathlib import Path

import pdfplumber
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentManager:
    """Save uploaded PDFs and prepare their text for retrieval and extraction."""

    def __init__(self, upload_dir="uploads", chunk_size=1000, chunk_overlap=200):
        self.upload_dir = Path(upload_dir).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.display_names = {}

    def save_uploaded_file(self, uploaded_file):
        """Save an uploaded PDF under a safe, content-addressed filename."""
        original_name = uploaded_file.name.replace("\\", "/").rsplit("/", 1)[-1]
        suffix = Path(original_name).suffix.lower()
        if suffix != ".pdf":
            raise ValueError(f"Only PDF files can be saved: {original_name}")

        file_bytes = uploaded_file.getvalue()
        if not file_bytes:
            raise ValueError(f"The uploaded file is empty: {original_name}")

        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(original_name).stem)
        safe_stem = safe_stem.strip("._-")[:100] or "document"
        content_hash = hashlib.sha256(file_bytes).hexdigest()
        saved_path = self.upload_dir / f"{content_hash}_{safe_stem}.pdf"

        if not saved_path.exists():
            saved_path.write_bytes(file_bytes)

        self.display_names[saved_path.name] = original_name
        return saved_path

    def save_uploaded_files(self, uploaded_files):
        """Save a collection of Streamlit UploadedFile objects."""
        return [self.save_uploaded_file(uploaded_file) for uploaded_file in uploaded_files]

    def list_saved_pdfs(self):
        """Find PDF files already stored in the uploads directory."""
        return sorted(
            (
                path
                for path in self.upload_dir.rglob("*")
                if path.suffix.lower() == ".pdf"
                and path.is_file()
                and not path.is_symlink()
            ),
            key=lambda path: str(path).casefold(),
        )

    def clear_all_files(self):
        """Delete files contained in uploads, leaving the directory in place."""
        deleted_count = 0
        for path in self.upload_dir.rglob("*"):
            if path.is_file() or path.is_symlink():
                path.unlink()
                deleted_count += 1
        return deleted_count

    def get_signature(self, file_paths):
        """Return a stable signature for the selected stored PDFs."""
        digest = hashlib.sha256()
        for file_path in sorted(
            (Path(path) for path in file_paths),
            key=lambda path: str(path),
        ):
            digest.update(file_path.name.encode("utf-8"))
        return digest.hexdigest()

    def get_display_name(self, file_path):
        """Return the uploaded filename without its internal content hash."""
        name = Path(file_path).name
        return self.display_names.get(
            name,
            re.sub(r"^[0-9a-f]{64}_", "", name, count=1),
        )

    def extract_pages(self, file_path):
        """Extract non-empty pages as LangChain documents with source metadata."""
        file_path = Path(file_path)
        page_documents = []

        with pdfplumber.open(file_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    page_documents.append(
                        Document(
                            page_content=page_text,
                            metadata={
                                "source": self.get_display_name(file_path),
                                "page": page_number,
                            },
                        )
                    )

        return page_documents

    def extract_text(self, file_path):
        """Extract all available text from a PDF as one string."""
        pages = self.extract_pages(file_path)
        return "\n\n".join(page.page_content for page in pages)

    def split_documents(self, documents):
        """Split LangChain documents into overlapping chunks."""
        return self.text_splitter.split_documents(documents)

    def process_pdf(self, file_path):
        """Extract and split one PDF for use in the vector store."""
        return self.split_documents(self.extract_pages(file_path))

    def process_pdfs(self, file_paths):
        """Extract and split a collection of PDFs."""
        chunks = []
        for file_path in file_paths:
            chunks.extend(self.process_pdf(file_path))
        return chunks
