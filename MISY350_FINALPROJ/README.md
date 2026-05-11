# Streamlit App Template

Template for students to clone and run quickly.
Open this repository folder itself in VS Code (not a parent directory that contains other `.venv` folders).
For full student instructions and troubleshooting, see `STEPS.md`.
If commands say `file does not exist`, run `cd ..` and then `cd streamlit-app-template` before retrying.

## Step 1 (One-Time Setup)
1. In Terminal, move into the project directory:
```bash
cd streamlit-app-template
```
2. Run setup:
- macOS/Linux:
```bash
python3 setup_script.py
```
- Windows:
```powershell
python setup_script.py
```
This will:
- create/reuse `.venv`
- install dependencies (`requirements.txt` if present, otherwise script defaults)
- set VS Code to use this folder's `.venv` interpreter

If `import streamlit` is still underlined in VS Code:
1. Open Command Palette (`Cmd+Shift+P` on macOS / `Ctrl+Shift+P` on Windows)
2. Run `Python: Select Interpreter`
3. Choose this project interpreter:
- macOS/Linux: `.venv/bin/python`
- Windows: `.venv\\Scripts\\python.exe`

## Step 2 (Run App)
1. Run starter:
- macOS/Linux:
```bash
python3 setup_starter.py
```
- Windows:
```powershell
python setup_starter.py
```
2. Keep terminal open while app is running.

## Run Without Starter Script
- macOS/Linux: `./.venv/bin/streamlit run app.py`
- Windows: `.\.venv\Scripts\streamlit.exe run app.py`

## Manual Setup (Alternative)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
