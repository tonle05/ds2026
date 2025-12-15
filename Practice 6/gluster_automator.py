#!/usr/bin/env python3
import os
import subprocess
import time
import shutil
import socket

# Configuration
BRICK_BASE_1 = "/data/brick1"
BRICK_BASE_2 = "/data/brick2"
BRICK_DIR_1 = os.path.join(BRICK_BASE_1, "gv0")
BRICK_DIR_2 = os.path.join(BRICK_BASE_2, "gv0")
MOUNT_POINT = "/mnt/gluster_client"
VOLUME_NAME = "gv0"
TEST_FILE_SIZE_MB = 512
SMALL_FILES_COUNT = 500

def get_real_ip():
    """Get the machine's real IP address (not 127.0.0.1)"""
    try:
        # Create a dummy UDP connection to determine the source IP selected by the OS
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print(f"[*] Detected Real IP: {ip}")
        return ip
    except Exception:
        # Fallback if no network is available: use hostname
        hostname = socket.gethostname()
        print(f"[*] Fallback to Hostname: {hostname}")
        return hostname

def run_command(cmd, shell=False, ignore_error=False):
    """Executes a shell command."""
    print(f"[*] Executing: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        subprocess.check_call(cmd, shell=shell)
    except subprocess.CalledProcessError as e:
        if not ignore_error:
            print(f"[!] Error: {e}")
            raise e
        else:
            print(f"[i] Ignored error (cleanup step): {e}")

def cleanup_previous_run():
    print("\n=== STEP 0: CLEANUP PREVIOUS DATA ===")
    
    print("-> Unmounting...")
    run_command(f"umount -f {MOUNT_POINT}", shell=True, ignore_error=True)
    
    print("-> Stopping and Deleting old volume...")
    # Add --mode=script to avoid Yes/No prompts
    run_command(["gluster", "--mode=script", "volume", "stop", VOLUME_NAME, "force"], ignore_error=True)
    run_command(["gluster", "--mode=script", "volume", "delete", VOLUME_NAME], ignore_error=True)
    
    print("-> Removing old brick data...")
    if os.path.exists(BRICK_BASE_1):
        shutil.rmtree(BRICK_BASE_1)
    if os.path.exists(BRICK_BASE_2):
        shutil.rmtree(BRICK_BASE_2)
        
    print("-> Restarting glusterd service...")
    run_command("systemctl restart glusterd", shell=True)
    time.sleep(2)

def setup_glusterfs(ip_address):
    print("\n=== STEP 1: INSTALL & SETUP GLUSTERFS ===")
    
    print("-> Creating fresh Brick directories...")
    os.makedirs(BRICK_DIR_1, exist_ok=True)
    os.makedirs(BRICK_DIR_2, exist_ok=True)
    os.makedirs(MOUNT_POINT, exist_ok=True)

    print(f"-> Creating Distributed Replicated Volume using IP: {ip_address}...")
    # Replace localhost with real IP
    cmd = [
        "gluster", "volume", "create", VOLUME_NAME, "replica", "2",
        f"{ip_address}:{BRICK_DIR_1}",
        f"{ip_address}:{BRICK_DIR_2}",
        "force"
    ]
    run_command(cmd)

    print("-> Starting volume...")
    run_command(["gluster", "volume", "start", VOLUME_NAME])

    print("-> Mounting volume...")
    # Mount using real IP
    run_command(f"mount -t glusterfs {ip_address}:/{VOLUME_NAME} {MOUNT_POINT}", shell=True)
    print(f"[OK] Volume mounted at {MOUNT_POINT}")

def benchmark_large_file():
    print("\n=== BENCHMARK 1: LARGE FILE (Read Speed) ===")
    filepath = os.path.join(MOUNT_POINT, "large_test_file.dat")
    
    print(f"-> Generating {TEST_FILE_SIZE_MB}MB file...")
    run_command(f"dd if=/dev/zero of={filepath} bs=1M count={TEST_FILE_SIZE_MB} status=progress", shell=True)
    
    print("-> Clearing RAM cache...")
    run_command("sync; echo 3 > /proc/sys/vm/drop_caches", shell=True)
    
    print("-> Reading file...")
    start_time = time.time()
    with open(filepath, 'rb') as f:
        while f.read(1024*1024): 
            pass
    end_time = time.time()
    
    duration = end_time - start_time
    speed = TEST_FILE_SIZE_MB / duration
    print(f"-> Result: {speed:.2f} MB/s")
    return speed

def benchmark_small_files():
    print("\n=== BENCHMARK 2: SMALL FILES (Accesses/s) ===")
    test_dir = os.path.join(MOUNT_POINT, "small_files")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir, exist_ok=True)
    
    print(f"-> Creating {SMALL_FILES_COUNT} small files...")
    start_time = time.time()
    for i in range(SMALL_FILES_COUNT):
        with open(os.path.join(test_dir, f"file_{i}"), 'w') as f:
            f.write("test")
    end_time = time.time()
    
    duration = end_time - start_time
    rate = SMALL_FILES_COUNT / duration
    print(f"-> Result: {rate:.2f} ops/s")
    return rate

def main():
    if os.geteuid() != 0:
        print("Please run as root (sudo).")
        return

    try:
        # Get real IP first
        real_ip = get_real_ip()
        
        cleanup_previous_run()
        setup_glusterfs(real_ip)
        
        l_speed = benchmark_large_file()
        s_rate = benchmark_small_files()
        
        print("\n" + "="*30)
        print("RESULTS FOR REPORT")
        print("="*30)
        print(f"Large Files Read: {l_speed:.2f} MB/s")
        print(f"Small Files Rate: {s_rate:.2f} ops/s")
        print("="*30)

    except Exception as e:
        print(f"\n[FATAL ERROR]: {e}")
        print("Please check if your network is active (ip addr show).")

if __name__ == "__main__":
    main()