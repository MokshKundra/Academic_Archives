import threading
import queue as queue_module
from jobs import process_upload_job

upload_queue = queue_module.Queue()

def _worker():
    while True:
        job_args = upload_queue.get()  
        try:
            process_upload_job(*job_args)
        finally:
            upload_queue.task_done()


_worker_thread = threading.Thread(target=_worker, daemon=True)
_worker_thread.start()

def enqueue_upload(job_id: str, tmp_path: str, course_id: str, doc_title: str, doc_type: str):
    upload_queue.put((job_id, tmp_path, course_id, doc_title, doc_type))

def queue_size() -> int:
    return upload_queue.qsize()