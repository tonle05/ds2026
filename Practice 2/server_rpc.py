# server_rpc.py
from xmlrpc.server import SimpleXMLRPCServer
import base64
from pathlib import Path
import os
import threading


RECV_DIR = Path("received_files")
RECV_DIR.mkdir(exist_ok=True)

# state for one active transfer (single-client simple implementation)
_state_lock = threading.Lock()
_state = {
    "file_obj": None,
    "filepath": None,
    "expected": 0,
    "received": 0,
    "active": False
}

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB limit (adjust as needed)

def start_transfer(filename, filesize):
    """
    Start a new transfer. Server will create a new file under received_files/.
    Returns "OK" or "ERROR: message".
    """
    with _state_lock:
        if _state["active"]:
            return "ERROR: another transfer in progress"
        try:
            filesize = int(filesize)
        except Exception:
            return "ERROR: invalid filesize"
        if filesize < 0 or filesize > MAX_FILE_SIZE:
            return f"ERROR: filesize out of allowed range (0..{MAX_FILE_SIZE})"

        safe_name = os.path.basename(filename)
        dest = RECV_DIR / safe_name
        # If file exists, choose a non-colliding name
        if dest.exists():
            base, ext = os.path.splitext(safe_name)
            i = 1
            while True:
                candidate = RECV_DIR / f"{base}_{i}{ext}"
                if not candidate.exists():
                    dest = candidate
                    break
                i += 1

        try:
            f = open(dest, "wb")
        except Exception as e:
            return f"ERROR: cannot open destination file: {e}"

        _state.update({
            "file_obj": f,
            "filepath": str(dest),
            "expected": filesize,
            "received": 0,
            "active": True
        })
        print(f"[SERVER] Start transfer -> {dest} ({filesize} bytes)")
        return "OK"

def send_chunk(chunk_b64):
    """
    Receive one base64-encoded chunk, decode and write to the active file.
    Returns "OK" or "ERROR: message".
    """
    with _state_lock:
        if not _state["active"] or _state["file_obj"] is None:
            return "ERROR: no active transfer"
        try:
            data = base64.b64decode(chunk_b64)
        except Exception as e:
            return f"ERROR: invalid base64 data: {e}"
        try:
            _state["file_obj"].write(data)
            _state["received"] += len(data)
        except Exception as e:
            return f"ERROR: write failed: {e}"

        # optional progress print (same line)
        print(f"[SERVER] received {_state['received']}/{_state['expected']}", end="\r")
        return "OK"

def finish():
    """
    Finish the current transfer: close file, validate size, optionally verify image.
    Returns "DONE | details" or "ERROR | details".
    """
    with _state_lock:
        if not _state["active"] or _state["file_obj"] is None:
            return "ERROR: no active transfer"
        try:
            _state["file_obj"].close()
        except Exception as e:
            return f"ERROR: closing file failed: {e}"
        filepath = _state["filepath"]
        rec = _state["received"]
        exp = _state["expected"]

        details = []
        ok = True
        if rec != exp:
            ok = False
            details.append(f"size_mismatch received={rec} expected={exp}")
        else:
            details.append(f"size_ok {rec} bytes")


        # reset state
        _state.update({
            "file_obj": None,
            "filepath": None,
            "expected": 0,
            "received": 0,
            "active": False
        })

        status = "DONE" if ok else "ERROR"
        msg = f"{status} | " + "; ".join(details)
        print("\n[SERVER] Transfer finished:", msg)
        return msg

if __name__ == "__main__":
    server = SimpleXMLRPCServer(("0.0.0.0", 8000), allow_none=True)
    server.register_function(start_transfer, "start_transfer")
    server.register_function(send_chunk, "send_chunk")
    server.register_function(finish, "finish")
    print("[SERVER] RPC File Transfer ready on port 8000")
    server.serve_forever()
