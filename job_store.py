import json
import uuid
from datetime import datetime
from pathlib import Path
from enum import Enum

JOBS_DIR = Path("./jobs")
JOBS_DIR.mkdir(exist_ok=True)

class JobStatus(str, Enum):
    QUEUED = "queued"
    EXTRACTING = "extracting"
    EMBEDDING = "embedding"
    DONE = "done"
    FAILED = "failed"

def create_job(course_id: str, doc_title: str, doc_type: str) -> str:
    job_id = str(uuid.uuid4())[:8]
    job = {
        "job_id": job_id,
        "status": JobStatus.QUEUED,
        "course_id": course_id,
        "doc_title": doc_title,
        "doc_type": doc_type,
        "progress": {"current_page": 0, "total_pages": None},
        "error": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    (JOBS_DIR / f"{job_id}.json").write_text(json.dumps(job, indent=2))
    return job_id

def update_job(job_id: str, **kwargs):
    path = JOBS_DIR / f"{job_id}.json"
    job = json.loads(path.read_text())
    job.update(kwargs)
    job["updated_at"] = datetime.now().isoformat()
    path.write_text(json.dumps(job, indent=2))

def get_job(job_id: str) -> dict:
    path = JOBS_DIR / f"{job_id}.json"
    if not path.exists():
        raise ValueError(f"Job {job_id} not found")
    return json.loads(path.read_text())

def list_jobs() -> list[dict]:
    return [json.loads(f.read_text()) for f in sorted(JOBS_DIR.glob("*.json"), reverse=True)]