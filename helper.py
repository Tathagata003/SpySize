# ...existing code...
import os
import concurrent.futures
# argparse removed per user request
import heapq
import time

def get_directory_size(path, cancel_event=None):
    """Calculates the total size of a directory in bytes."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path, onerror=lambda e: None, followlinks=False):
        if cancel_event is not None and cancel_event.is_set():
            break
        
        for f in filenames:
            if cancel_event is not None and cancel_event.is_set():
                break

            fp = os.path.join(dirpath, f)
            # Skip symbolic links
            if os.path.islink(fp):
                continue
            # Use os.path.getsize to get file size, handle potential errors
            try:
                total_size += os.path.getsize(fp)
            except OSError:
                # Handle cases where files might be inaccessible or broken links
                pass
    return total_size

def find_largest_directories(root_dir, num_largest=10, max_workers=None, cancel_event=None):
    """
    Finds the largest subdirectories within a given root directory using multithreading.

    Args:
        root_dir (str): The path to the root directory to scan.
        num_largest (int): The number of largest directories to return.
        max_workers (int|None): Number of worker threads for parallel scanning (None => automatic).
        cancel_event (threading.Event|None): If set, stops processing futures early.

    Returns:
        list: A list of tuples (directory_path, size_in_bytes) of the largest directories.
    """
    if not os.path.isdir(root_dir):
        # print(f"Error: '{root_dir}' is not a valid directory.")
        return []

    try:
        entries = os.listdir(root_dir)
    except OSError:
        # print(f"Error: cannot access directory '{root_dir}'.")
        return []

    # Prepare list of immediate subdirectories (skip symlinks)
    subdirs = []
    for item in entries:
        item_path = os.path.join(root_dir, item)
        if os.path.isdir(item_path) and not os.path.islink(item_path):
            subdirs.append(item_path)

    dir_sizes = {}
    if subdirs and num_largest != 0:
        # Choose a reasonable default for max_workers
        if max_workers is None:
            cpu = os.cpu_count() or 1
            max_workers = min(32, cpu * 5)

        # Compute sizes in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as exc:
            future_to_path = {exc.submit(get_directory_size, p, cancel_event): p for p in subdirs}
            
            
            while future_to_path:
            # Wait with a 1-second timeout so we check cancellation frequently
                done, pending = concurrent.futures.wait(future_to_path.keys(), timeout=1.0)
                
                # Check cancellation
                if cancel_event is not None and cancel_event.is_set():
                    for f in pending:
                        f.cancel()
                    break
                
                # Process completed futures
                for fut in done:
                    p = future_to_path[fut]
                    try:
                        dir_sizes[p] = fut.result()
                    except Exception:
                        dir_sizes[p] = 0
                    del future_to_path[fut]
    
    sorted_dirs = sorted(dir_sizes.items(), key=lambda item: item[1], reverse=True)
    return sorted_dirs[:num_largest]

def find_largest_files(root_dir, num_files=10, cancel_event=None):
    """
    Finds the largest files under root_dir (recursive).

    Args:
        root_dir (str): Path to scan.
        num_files (int): Number of largest files to return.
        cancel_event (threading.Event|None): If set, stops scanning early.

    Returns:
        list: A list of tuples (file_path, size_in_bytes) of the largest files.
    """
    if num_files == 0:
        return []

    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir, onerror=lambda e: None, followlinks=False):
        if cancel_event is not None and cancel_event.is_set():
            break
        
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.islink(fp):
                continue
            try:
                size = os.path.getsize(fp)
            except OSError:
                continue
            files.append((size, fp))

    if not files:
        return []

    top = heapq.nlargest(num_files, files, key=lambda x: x[0])
    # convert to (path, size)
    return [(p, s) for s, p in top]

def format_size(size_in_bytes):
    """Formats a size in bytes into a human-readable string (KB, MB, GB)."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024**2:
        return f"{size_in_bytes / 1024:.2f} KB"
    elif size_in_bytes < 1024**3:
        return f"{size_in_bytes / (1024**2):.2f} MB"
    else:
        return f"{size_in_bytes / (1024**3):.2f} GB"

"""
if __name__ == "__main__":
    # argparse removed per user request; main-runner is commented out
    # parser = argparse.ArgumentParser(description="Find largest subdirectories and files.")
    # parser.add_argument("-p", "--path", required=True,
    #                     help="Root directory to scan (required)")
    # parser.add_argument("--return-folders-num", dest="folders_num", type=int, default=10,
    #                     help="Number of largest subdirectories to return (default: 10)")
    # parser.add_argument("--return-files-num", dest="files_num", type=int, default=10,
    #                     help="Number of largest files to return (default: 10)")
    # args = parser.parse_args()

    # target_directory = os.path.abspath(os.path.expanduser(args.path))

    # start_total = time.perf_counter()

    # # sanitize requested numbers
    # folders_requested = max(0, args.folders_num)
    # files_requested = max(0, args.files_num)

    # # count available immediate subdirectories (skip symlinks)
    # try:
    #     entries = os.listdir(target_directory)
    # except OSError:
    #     # print(f"Error: cannot access directory '{target_directory}'.")
    #     raise SystemExit(1)

    # immediate_subdirs = [os.path.join(target_directory, item)
    #                      for item in entries
    #                      if os.path.isdir(os.path.join(target_directory, item)) and not os.path.islink(os.path.join(target_directory, item))]
    # available_subdirs_count = len(immediate_subdirs)

    # # adjust requested folders if fewer available
    # folders_to_request = min(folders_requested, available_subdirs_count)

    # if available_subdirs_count == 0:
    #     # print("No immediate subdirectories found.")
    #     largest_dirs = []
    # else:
    #     # print(f"Working: scanning {available_subdirs_count} subdirectories (returning top {folders_to_request})...")
    #     t0 = time.perf_counter()
    #     largest_dirs = find_largest_directories(target_directory, num_largest=folders_to_request)
    #     t1 = time.perf_counter()
    #     # print(f"Finished scanning folders in {t1 - t0:.2f}s.")

    # if largest_dirs:
    #     actual_folders = len(largest_dirs)
    #     # print(f"Top {actual_folders} largest subdirectories in '{target_directory}':")
    #     for dir_path, size in largest_dirs:
    #         # print(f"- {dir_path}: {format_size(size)}")
    # else:
    #     # print("No subdirectories found or an error occurred.")

    # # find files
    # if files_requested == 0:
    #     # print("\nSkipping file scan (requested 0).")
    #     largest_files = []
    # else:
    #     # print(f"\nWorking: scanning files recursively (returning top {files_requested})...")
    #     t0 = time.perf_counter()
    #     largest_files = find_largest_files(target_directory, num_files=files_requested)
    #     t1 = time.perf_counter()
    #     # print(f"Finished scanning files in {t1 - t0:.2f}s.")

    # if largest_files:
    #     actual_files = len(largest_files)
    #     # print(f"\nTop {actual_files} largest files in '{target_directory}':")
    #     for file_path, size in largest_files:
    #         # print(f"- {file_path}: {format_size(size)}")
    # else:
    #     # print("\nNo files found or an error occurred.")

    # end_total = time.perf_counter()
    # # print(f"\nTotal elapsed time: {end_total - start_total:.2f}s")
"""
