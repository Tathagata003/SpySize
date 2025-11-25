# Folder Size Scanner

Small utility to find the largest subdirectories and files in a folder. The project contains a reusable helper module with the scanning logic and a small Tkinter GUI wrapper that calls the helper functions and streams results to the UI.

## Repo layout

- `helper.py` — core logic (directory/file scanning, multithreaded folder size computation, formatting). The `if __name__ == '__main__'` runner / argparse has been removed or commented out so the module is import-safe for the GUI and packaging.
- `gui_runner.py` — Tkinter GUI that imports `helper` and provides:
  - Path browse dialog
  - Fields for "Return folders (num)" and "Return files (num)"
  - A Start button that runs the scan on a background thread and streams progress into a Text box
- `main.py.py` — earlier CLI iterations (may be present). Prefer `helper.py` + `gui_runner.py` now.


## Features

- Recursive file scan (top N largest files).
- Multithreaded immediate-subdirectory size scan using ThreadPoolExecutor (top N largest folders).
- Thread-safe GUI updates via `root.after(...)` so results stream progressively to the Text widget.
- Helpful functions exported from `helper.py`:
  - `get_directory_size(path)`
  - `find_largest_directories(root_dir, num_largest=10, max_workers=None)`
  - `find_largest_files(root_dir, num_files=10)`
  - `format_size(size_in_bytes)`


## Requirements

- Python 3.8+ (tested on Windows)
- Tkinter (usually included with standard Python on Windows)
- PyInstaller (for building the exe)

Install PyInstaller in your environment:

```powershell
pip install pyinstaller
```


## Run the GUI (development)

From project folder:

```powershell
python .\gui_runner.py
```

- Click "Browse..." and select a folder.
- Optionally adjust "Return folders (num)" and "Return files (num)" (defaults to 10).
- Click "Start scan". Progress messages and results will appear in the text area as they become available.


## Build a single-file exe with PyInstaller

Typical command (from project root):

```powershell
pyinstaller --onefile --windowed gui_runner.py --name SizeFinder --clean
```

- `--onefile` bundles into a single exe (this is when PyInstaller appends the PYZ payload into the exe).
- `--windowed` hides the console and shows only the GUI window.
- `--clean` removes temporary build state before building.

If you run into permission or "append to exe" errors (common on Windows), see Troubleshooting below.


## Build alternatives and diagnostics

- Build to a different `dist` path to avoid overwriting a locked exe:

```powershell
pyinstaller --onefile --windowed gui_runner.py --name SizeFinder --clean --distpath "D:\temp_dist" --log-level=DEBUG
```

- Build a one-folder distribution instead (avoids the append step and is useful for debugging):

```powershell
pyinstaller --onedir --windowed gui_runner.py --name SizeFinder --clean
```

- If a onefile build fails repeatedly, try `--noupx` to disable UPX packing:

```powershell
pyinstaller --onefile --windowed gui_runner.py --name SizeFinder --clean --noupx
```


## Troubleshooting: PermissionError / append_data_to_exe

I did this step to stop the permission issue
To allow access to a folder in K7 Total Security, go to Settings > Antivirus and AntiSpyware > Real-Time Protection > manage exclusions. Click Add Entry, then Add Folder to browse and select the folder, and check the boxes for Exclude from Real-Time Scanner and any other desired options before clicking OK to save.

Common causes and fixes (ordered):

1. The exe is currently running. Close it (Task Manager) or run:

```powershell
Stop-Process -Name SizeFinder -ErrorAction SilentlyContinue -Force
taskkill /IM SizeFinder.exe /F
```

2. Explorer or a terminal is holding a handle to the dist folder. Close Explorer windows that show the folder (or restart Explorer):

```powershell
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Process explorer
```

3. Delete the `dist` and `build` folders before rebuilding:

```powershell
Remove-Item -LiteralPath 'D:\python\folder size\dist' -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'D:\python\folder size\build' -Recurse -Force -ErrorAction SilentlyContinue
```

4. Antivirus or real-time protection (e.g. K7 Total Security) may lock or intercept newly created exes. Add the project folder to exclusions in your AV and, if required, restart the AV or the machine.

5. If deletion or access is denied, take ownership / fix ACLs (Admin):

```powershell
takeown /F "D:\python\folder size\dist" /A /R
icacls "D:\python\folder size\dist" /grant "$env:USERNAME:F" /T
```

6. Use Sysinternals `handle.exe` (Admin) or Resource Monitor to find the process holding the handle:

```powershell
# run handle.exe from its directory
.\handle.exe SizeFinder.exe
```

7. If all else fails, reboot the system to clear locks.


## Notes for packaging

- `helper.py` has been made import-safe (no active argparse runner) so `gui_runner.py` can import it without argparse executing during PyInstaller analysis.
- If you want to keep a CLI runner, re-add a small guarded `if __name__ == '__main__'` block in a separate script so importing `helper` remains side-effect free.


## Suggestions / further improvements

- Add an optional per-directory progress callback to `find_largest_directories` so `gui_runner.py` can show each directory size as it completes (currently the GUI shows folders after the ThreadPool finishes).
- Add a Cancel button to the GUI and cooperative cancellation (a shared Event/flag checked by the worker and size calculators).
- Add logging to a file for long-running scans.


## Contact / Next steps

If you want, I can:

- Add a `README.md` file into the repo (done).
- Implement the per-directory progress callback and wire it into `gui_runner.py` (I can edit `helper.py` and `gui_runner.py`).
- Run the PyInstaller build in your workspace and fix any remaining build-time errors interactively.

Tell me which of the above you'd like me to do next.
