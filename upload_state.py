import threading

_active_uploads = 0
_lock = threading.Lock()

def upload_started():
    global _active_uploads
    with _lock:
        _active_uploads += 1

def upload_finished():
    global _active_uploads
    with _lock:
        _active_uploads = max(0, _active_uploads - 1)

def is_upload_in_progress() -> bool:
    with _lock:
        return _active_uploads > 0