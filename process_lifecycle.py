"""Radio & TV Segmenter — Subprocess tracking and OS-level job object lifecycle isolation.

Guarantees clean child process termination (FFmpeg, Whisper, PyAnnote, plugins)
upon application exit or unexpected crashes via Windows Job Objects and process registries.
"""

from __future__ import annotations

import sys

try:
    from PySide6.QtCore import QProcess
except ImportError:
    QProcess = None

_REGISTERED_PROCESSES = set()
_WINDOWS_JOB_HANDLE = None


def init_child_process_job_isolation():
    """Initialize OS-level guarantees that child processes terminate when parent exits.
    On Windows: Configures a Job Object with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE.
    """
    global _WINDOWS_JOB_HANDLE
    if sys.platform == "win32" and _WINDOWS_JOB_HANDLE is None:
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.windll.kernel32

            # Job object creation and limits
            CreateJobObjectW = kernel32.CreateJobObjectW
            CreateJobObjectW.restype = wintypes.HANDLE
            CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]

            SetInformationJobObject = kernel32.SetInformationJobObject
            SetInformationJobObject.restype = wintypes.BOOL

            AssignProcessToJobObject = kernel32.AssignProcessToJobObject
            AssignProcessToJobObject.restype = wintypes.BOOL
            AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]

            GetCurrentProcess = kernel32.GetCurrentProcess
            GetCurrentProcess.restype = wintypes.HANDLE

            job = CreateJobObjectW(None, None)
            if job:
                # JobObjectExtendedLimitInformation = 9
                JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

                class IO_COUNTERS(ctypes.Structure):
                    _fields_ = [
                        ("ReadOperationCount", ctypes.c_uint64),
                        ("WriteOperationCount", ctypes.c_uint64),
                        ("OtherOperationCount", ctypes.c_uint64),
                        ("ReadTransferCount", ctypes.c_uint64),
                        ("WriteTransferCount", ctypes.c_uint64),
                        ("OtherTransferCount", ctypes.c_uint64),
                    ]

                class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
                    _fields_ = [
                        ("PerProcessUserTimeLimit", ctypes.c_int64),
                        ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t),
                        ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD),
                    ]

                class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
                    _fields_ = [
                        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                        ("IoInfo", IO_COUNTERS),
                        ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryLimit", ctypes.c_size_t),
                        ("PeakJobMemoryLimit", ctypes.c_size_t),
                    ]

                info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
                info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

                if SetInformationJobObject(
                    job,
                    9,  # JobObjectExtendedLimitInformation
                    ctypes.byref(info),
                    ctypes.sizeof(info),
                ):
                    # Assign the current parent process to this job so all child processes
                    # automatically inherit the job assignment
                    AssignProcessToJobObject(job, GetCurrentProcess())
                    _WINDOWS_JOB_HANDLE = job
        except Exception:
            _WINDOWS_JOB_HANDLE = None


def bind_subprocess_to_job(proc):
    """Assign an individual process (by HANDLE or PID) to the Windows Job Object if needed."""
    if sys.platform == "win32" and _WINDOWS_JOB_HANDLE:
        try:
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            OpenProcess = kernel32.OpenProcess
            OpenProcess.restype = wintypes.HANDLE
            OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            CloseHandle = kernel32.CloseHandle
            CloseHandle.restype = wintypes.BOOL
            CloseHandle.argtypes = [wintypes.HANDLE]
            AssignProcessToJobObject = kernel32.AssignProcessToJobObject
            AssignProcessToJobObject.restype = wintypes.BOOL
            AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]

            pid = None
            if hasattr(proc, "pid"):
                p = proc.pid
                pid = p() if callable(p) else p
            elif hasattr(proc, "processId"):
                pid = proc.processId()

            if pid and pid > 0:
                PROCESS_SET_QUOTA = 0x0100
                PROCESS_TERMINATE = 0x0001
                h_proc = OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, int(pid))
                if h_proc:
                    AssignProcessToJobObject(_WINDOWS_JOB_HANDLE, h_proc)
                    CloseHandle(h_proc)
        except Exception:
            pass


def register_process(proc):
    """Register a QProcess or subprocess.Popen instance to track its lifecycle."""
    if proc is not None:
        _REGISTERED_PROCESSES.add(proc)
        bind_subprocess_to_job(proc)


def unregister_process(proc):
    """Unregister a process when it exits naturally or is cleaned up."""
    _REGISTERED_PROCESSES.discard(proc)


def terminate_all_registered_processes():
    """Terminate and wait on all active child processes upon application close."""
    for proc in list(_REGISTERED_PROCESSES):
        if proc is None:
            continue
        try:
            # Handle PySide6 QProcess
            if hasattr(proc, "state"):
                if QProcess is not None and proc.state() != QProcess.ProcessState.NotRunning:
                    proc.terminate()
                    if not proc.waitForFinished(300):
                        proc.kill()
                        proc.waitForFinished(300)
                elif hasattr(proc, "terminate"):
                    proc.terminate()
            # Handle standard Python subprocess.Popen
            elif hasattr(proc, "poll") and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=0.3)
                except Exception:
                    proc.kill()
        except Exception:
            pass
    _REGISTERED_PROCESSES.clear()


# Initialize Job Object isolation on Windows as early as possible
try:
    init_child_process_job_isolation()
except Exception:
    pass
