import os
from job_store import update_job, JobStatus
from pdf_upload import extractor
from upload_schema import Document
from upload import addToCousreCollection
import threading
from upload_state import upload_started, upload_finished


ollama_lock = threading.Lock()

def process_upload_job(job_id: str, tmp_path: str, course_id: str, doc_title: str, doc_type: str):
    upload_started()
    try:
        update_job(job_id, status=JobStatus.EXTRACTING)

        with ollama_lock:
            def progress_callback(current, total):
                update_job(job_id, progress={"current_page": current, "total_pages": total})

            extracted_content = extractor(tmp_path, doc_title, on_page_done=progress_callback)

        update_job(job_id, status=JobStatus.EMBEDDING)

        with ollama_lock:
            doc = Document(
                course_id=course_id,
                doc_title=doc_title,
                doc_type=doc_type,
                content=extracted_content
            )
            addToCousreCollection(doc)

        update_job(job_id, status=JobStatus.DONE)

    except Exception as e:
        update_job(job_id, status=JobStatus.FAILED, error=str(e))
    finally:
        upload_finished()
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)