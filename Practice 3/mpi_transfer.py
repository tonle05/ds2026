#!/usr/bin/env python3
# Usage examples (requires mpi4py and an MPI runtime, e.g. OpenMPI/MPICH):
#   mpirun -np 2 python3 mpi_transfer.py send test.txt
#   mpirun -np 3 python3 mpi_transfer.py send file_for_rank1.txt file_for_rank2.txt
# Notes:
#  - Rank 0 is the receiver (server).
#  - Ranks >=1 are senders (clients). Each sender should provide its file path
#    as a separate command-line argument in the order of ranks (rank 1 -> arg2, rank 2 -> arg3, ...).
#  - The received files are saved as: received_from_rank<r>_<original_filename>

from mpi4py import MPI
import sys, os

CHUNK = 4096
TAG_NAME_LEN = 1
TAG_NAME = 2
TAG_SIZE = 3
TAG_DATA = 4
TAG_DONE = 5

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def sender(filepath, dest=0):
    if not os.path.isfile(filepath):
        print(f"[rank {rank}][SENDER] File not found: {filepath}", flush=True)
        comm.Abort(1)
    fname = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)

    # Print sending notice BEFORE actual send for clearer logs
    print(f"[rank {rank}][SENDER] Sending '{fname}' ({filesize} bytes) to rank {dest}...", flush=True)

    # send name length then name
    namelen = len(fname) + 1  # include null-like terminator length (not strictly needed)
    comm.send(namelen, dest=dest, tag=TAG_NAME_LEN)
    comm.Send([fname.encode('utf-8'), MPI.CHAR], dest=dest, tag=TAG_NAME)
    # send filesize (as Python int)
    comm.send(filesize, dest=dest, tag=TAG_SIZE)
    # send data in chunks
    with open(filepath, 'rb') as f:
        sent = 0
        while sent < filesize:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            # send raw bytes
            comm.Send([chunk, MPI.BYTE], dest=dest, tag=TAG_DATA)
            sent += len(chunk)
    # notify done
    comm.send(True, dest=dest, tag=TAG_DONE)
    # final confirmation after send completes
    print(f"[rank {rank}][SENDER] Done sending '{fname}' ({filesize} bytes) to rank {dest}.", flush=True)

def receiver(n_senders):
    # expect n_senders sends (from ranks 1..n_senders)
    for expected_from in range(1, n_senders+1):
        # receive name length
        namelen = comm.recv(source=expected_from, tag=TAG_NAME_LEN)
        # receive name
        # allocate a buffer to receive chars
        # MPI.Recv with MPI.CHAR expects a writable buffer; use bytearray
        name_buf = bytearray(namelen)
        comm.Recv([name_buf, MPI.CHAR], source=expected_from, tag=TAG_NAME)
        # decode up to first zero or full length
        try:
            fname = name_buf.rstrip(b'\x00').decode('utf-8')
        except:
            fname = name_buf.decode('utf-8', errors='ignore')
        # receive filesize
        filesize = comm.recv(source=expected_from, tag=TAG_SIZE)
        out_name = f"received_from_rank{expected_from}_{fname}"
        print(f"[rank {rank}][RECV] Receiving '{fname}' ({filesize} bytes) from rank {expected_from} -> '{out_name}'", flush=True)
        received = 0
        with open(out_name, 'wb') as out:
            while received < filesize:
                # Probe for next incoming message
                status = MPI.Status()
                comm.Probe(source=expected_from, tag=MPI.ANY_TAG, status=status)
                t = status.Get_tag()
                if t == TAG_DATA:
                    count = status.Get_count(MPI.BYTE)
                    buf = bytearray(count)
                    comm.Recv([buf, MPI.BYTE], source=expected_from, tag=TAG_DATA, status=status)
                    out.write(buf)
                    received += count
                elif t == TAG_DONE:
                    # consume the done message and break
                    _ = comm.recv(source=expected_from, tag=TAG_DONE)
                    break
                else:
                    # unexpected tag; try to consume and continue
                    comm.recv(source=expected_from, tag=t)
        print(f"[rank {rank}][RECV] Done '{out_name}' ({received} bytes).", flush=True)

def main():
    if len(sys.argv) < 2:
        if rank == 0:
            print("Usage (called under mpirun):", flush=True)
            print("  mpirun -np 2 python3 mpi_transfer.py send test.txt", flush=True)
            print("  mpirun -np 3 python3 mpi_transfer.py send file_for_rank1.txt file_for_rank2.txt", flush=True)
        sys.exit(0)

    mode = sys.argv[1]
    if mode == "send":
        # map each sender rank to an argv index: rank 1 -> argv[2], rank 2 -> argv[3], ...
        if rank == 0:
            # receiver: count how many senders we expect
            n_senders = max(0, size - 1)
            if n_senders == 0:
                print("[RECV] No senders available (need at least 2 processes).", flush=True)
                comm.Abort(1)
            receiver(n_senders)
        else:
            # argv[2] for rank1 => arg_index = rank + 1
            arg_index = rank + 1
            if arg_index >= len(sys.argv):
                print(f"[rank {rank}][SENDER] Missing filepath argument for this sender. Expected argument index {arg_index}.", flush=True)
                comm.Abort(1)
            filepath = sys.argv[arg_index]
            sender(filepath)
    else:
        if rank == 0:
            print("Unknown mode. Only 'send' is supported.", flush=True)

if __name__ == "__main__":
    main()
