"""Native runtime bootstrap for the ML stack.

The scikit-learn Windows wheel ships its own copies of the MSVC C++ and OpenMP
runtimes in ``sklearn/.libs`` and force-loads them from
``sklearn/_distributor_init.py`` during ``import sklearn``. Those bundled images
win the loader race for every later native import in the process, and they are
older than the runtimes TensorFlow and PyTorch are linked against. Once
scikit-learn is imported first, both frameworks fail to initialise with:

    ImportError: DLL load failed ... A dynamic link library (DLL)
    initialization routine failed.        # 0x45A, DllMain returned false

Importing this module *before* scikit-learn loads the operating system copies of
those runtimes, so every framework in the process binds to the same images. It
is a no-op on non-Windows platforms and on machines without the DLLs present.
"""

import os
import sys

_SYSTEM_RUNTIME_DLLS = ("msvcp140.dll", "vcomp140.dll")


def _system32_dir() -> str:
    system_root = os.environ.get("SystemRoot") or os.environ.get("WINDIR") or r"C:\Windows"
    return os.path.join(system_root, "System32")


def preload_system_runtime() -> None:
    """Pin the MSVC runtime DLLs to the copies shipped with Windows."""
    if sys.platform != "win32":
        return

    system32 = _system32_dir()
    for name in _SYSTEM_RUNTIME_DLLS:
        path = os.path.join(system32, name)
        if not os.path.exists(path):
            continue
        try:
            import ctypes

            ctypes.WinDLL(path)
        except Exception:
            continue


preload_system_runtime()