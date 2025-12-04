# client_rpc.py
import xmlrpc.client
import base64
import os
import sys

if len(sys.argv) != 2:
    print("Usage: python3 client_rpc.py <file-to-send>")
    sys.exit(1)

filename = sys.argv[1]
if not os.path.exists(filename):
    print("File not found:", filename)
    sys.exit(1)

proxy = xmlrpc.client.ServerProxy("http://localhost:8000/", allow_none=True)

filesize = os.path.getsize(filename)
basename = os.path.basename(filename)
print(f"[CLIENT] file={filename} size={filesize} bytes")

# 1) start_transfer
resp = proxy.start_transfer(basename, filesize)
if not isinstance(resp, str) or not resp.startswith("OK"):
    print("Server refused start:", resp)
    sys.exit(1)

# 2) send chunks
CHUNK = 64 * 1024  # 64KB chunk size for efficiency; adjust if needed
sent = 0
with open(filename, "rb") as f:
    while True:
        chunk = f.read(CHUNK)
        if not chunk:
            break
        b64 = base64.b64encode(chunk).decode()
        resp = proxy.send_chunk(b64)
        if not isinstance(resp, str) or not resp.startswith("OK"):
            print("\nServer returned error during send_chunk:", resp)
            sys.exit(1)
        sent += len(chunk)
        print(f"[CLIENT] sent {sent}/{filesize}", end="\r")

# 3) finish
result = proxy.finish()
print("\n[CLIENT] finish response:", result)
