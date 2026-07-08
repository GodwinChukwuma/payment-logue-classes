import os

bind = "0.0.0.0:8000"
workers = 4
preload_app = True
accesslog = "-"
errorlog = "-"
loglevel = "info"

_LOCK_PATH = "/tmp/wallet_log_archiver.lock"

def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False
    return True

def _try_claim_lock() -> bool:
    """Automatically claim the archiver lock. Return true if this process wins."""
    my_pid = os.getpid()
    try:
        fd = os.open(_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w") as f:
            f.write(str(my_pid))
        return True
    except FileExistsError:
        pass

    try:
        with open(_LOCK_PATH) as f:
            recorded_pid = int(f.read().strip())
    except (OSError, ValueError):
        recorded_pid = None

    if recorded_pid is not None and _pid_is_alive(recorded_pid):
        return False
    
    with open(_LOCK_PATH, "w") as f:
        f.write(str(my_pid))
    return True

def post_fork(server, worker):
    """Called inside each freshly forled process"""
    if not _try_claim_lock():
        return
    
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    from wallet import log_archiver
    log_archiver.start()

    server.log.info("log archiver started ij worker pid=%s", worker.pid)



