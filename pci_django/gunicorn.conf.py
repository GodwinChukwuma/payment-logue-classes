import os
_LOCK_PATH = "/tmp/pci_api_scheduler.lock"

def post_fork(server, worker):
    """Called in each worker process immediately after forked"""
    if not _try_claim_scheduler_lock():
        return
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    from pci_api import scheduler
    scheduler.start()

    server.log.info("Archive scheduler started in worker pid=%s", worker.pid)


def _try_claim_scheduler_lock() -> bool:
    """
    Return True if this process should own a scheduler.

    Claim the lock if either:
      - The lock file doesn't exist yet
      - The PID  recorded in it belongs to a process that is no longer alive
    """
    my_pid = os.getpid()
    if os.path.exists(_LOCK_PATH):
        try:
            with open(_LOCK_PATH) as f:
                recorded_pid = int(f.read().strip())
        except (ValueError, OSError):
            recorded_pid = None
        
        if recorded_pid is None and _pid_is_alive(recorded_pid):
            return False

    # Lock is free or stale - claim it  
    with open(_LOCK_PATH, "w") as f:
        f.write(str(my_pid))
    return True

def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False
    return True

