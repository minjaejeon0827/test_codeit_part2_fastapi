# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Health-Eat** (PILL SIGHT) is a YOLO-based real-time pill detection and classification system. It combines a FastAPI backend server with a Streamlit frontend to enable users to upload pill images for AI-powered detection with built-in secure coding protections against file-based attacks.

**Primary Language**: Python (Korean comments/documentation)  
**Repository**: https://github.com/minjaejeon0827/test_Streamlit

## Architecture

### High-Level Design

The application uses a **dual-process architecture** managed by a single entry point:

1. **FastAPI Backend** (Port 8000): RESTful API server handling image processing and validation
   - Secure image re-encoding to prevent stealth malware embedded in files
   - Image format validation (JPEG, PNG, WEBP only)
   - Prepared for YOLO model integration

2. **Streamlit Frontend** (Port 8501): Interactive web UI for user interactions
   - File upload interface with drag-and-drop support
   - Server connection status monitoring
   - Pill detection results display
   - Custom CSS styling for enhanced UX

3. **Process Manager** (`run.py`): Spawns and manages both services simultaneously
   - Signal handling for graceful shutdown (SIGINT, SIGTERM)
   - Service startup verification with timeouts
   - Environment variable configuration (PYTHONPATH injection)

### Directory Structure

```
streamlit/
├── run.py                  # Entry point: launches FastAPI + Streamlit processes
├── src/
│   └── server.py          # FastAPI application with /detect endpoint
├── views/
│   └── main_page.py       # Streamlit frontend UI
├── public/
│   ├── css/
│   │   └── main.css       # Custom Streamlit styling (file uploader, layout, buttons)
│   └── images/            # UI banners and assets
├── make_fake_file.py      # Security testing: generates stealth attack payloads
└── .streamlit_env/        # Python virtual environment
```

### Core Dependencies

**Backend**:
- `fastapi==0.104.1` - Web framework
- `uvicorn==0.27.0.post1` - ASGI server
- `pillow` - Image processing/validation

**Frontend**:
- `streamlit==1.52.2` - Web app framework
- `requests` - HTTP client for API communication

## Running the Application

### Prerequisites

- Python 3.10+
- Virtual environment activated: `.streamlit_env\Scripts\activate` (Windows) or `.streamlit_env/bin/activate` (Unix)
- Dependencies installed via pip

### Development Startup

**Single command to run both services**:
```bash
python run.py
```

This will:
1. Start FastAPI server on `http://0.0.0.0:8000` (reloads on code changes)
2. Start Streamlit app on `http://0.0.0.0:8501` (headless mode enabled)
3. Handle graceful shutdown on Ctrl+C

**Manual startup** (separate terminals if needed):

FastAPI:
```bash
cd src
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Streamlit:
```bash
cd views
streamlit run main_page.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
```

### Configuration Notes

- **Host binding**: Currently `0.0.0.0` to allow Docker containers, mobile devices (same Wi-Fi), and cloud deployments. For local-only development, change to `127.0.0.1`.
- **Frontend localhost hardcoded**: `main_page.py` line 17 uses `http://127.0.0.1:8000/` for API calls - update if backend host changes.

## Key Implementation Details

### Backend Image Security (`src/server.py`)

The `/detect` endpoint implements **secure image re-encoding** to prevent attacks:

1. **Reads uploaded file into memory** (not disk)
2. **Opens with PIL** to validate it's a real image (catches fake executables disguised as images)
3. **Validates format** against whitelist (JPEG, PNG, WEBP only)
4. **Re-encodes image** to clean BytesIO buffer (strips malicious payloads hidden in file metadata/EOF)
5. **Returns cleaned bytes** for downstream AI processing

This defeats:
- `.exe` files with `.jpg` extension
- PHP webshells appended to EOF of valid JPEG
- BMP files with `.jpg` extension
- Stealth payloads in file metadata

### Frontend UI (`views/main_page.py`)

- **Streamlit session state**: Manages uploader key to reset file input on "Close" button
- **Server health check**: Sidebar indicator shows real-time API connectivity
- **Error handling**: Extracts and displays detailed error messages from FastAPI responses
- **Async-like UI**: Uses spinners during detection to indicate processing

### Styling (`public/css/main.css`)

Heavy customization of Streamlit's default components:
- File uploader: Fixed 200px height, centered button, custom Korean text
- Images: Center-aligned with auto width/height
- Buttons: Full-width with hover effects
- Sidebar padding: Aligned with main content

## Development Workflow

### Common Tasks

**Modify API endpoints**:
- Edit `src/server.py` → auto-reloads via Uvicorn
- Update `ALLOWED_IMAGE_FORMATS` list for new image types
- Always catch `HTTPException` for proper error propagation to frontend

**Modify frontend UI**:
- Edit `views/main_page.py` → auto-reloads via Streamlit
- Use `st.session_state` for persistent UI state across reruns
- Test CSS changes in `public/css/main.css` (reload browser)

**Test security measures**:
- Run `python make_fake_file.py` to generate stealth payloads
- Upload generated files to UI to verify detection blocks them
- Files created: `hack_test_stealth.jpg`, `hack_test_unallowed_format.jpg`

### Debugging

**To see detailed logs**:
- Remove `stdout=subprocess.PIPE` comments in `run.py` (currently disabled to avoid log mangling)
- FastAPI logs appear in terminal if parent process stdout is not captured
- Streamlit logs go to terminal as well

**Session state issues**:
- Streamlit reruns entire script on state changes; check `st.session_state` in conditionals
- Use `key` parameter on widgets to maintain state across reruns

**API connectivity**:
- Verify both services are running (ports 8000 and 8501)
- Check sidebar indicator in Streamlit UI shows "🟢 서버 연결됨" (green, connected)
- Test directly: `curl http://127.0.0.1:8000/` should return status JSON

## Git Conventions

Use Korean commit messages to match the project convention (e.g., `chore: 테스트 로직 수정`, `feat: 이미지 업로드 기능 추가`).

## Important Caveats

1. **Localhost hardcoded in frontend**: If backend URL changes, update line 17 in `main_page.py`
2. **Virtual environment not committed**: `.streamlit_env/` is local only; ensure dependencies are pip-installed
3. **Test attack files**: `hack_test_*.jpg/bmp` files are intentional security test payloads; do not delete
4. **No production config**: Current setup binds to `0.0.0.0` for development; use firewall/reverse proxy for production
5. **Headless mode**: Streamlit runs with `--server.headless true` to skip email prompt; required for non-interactive startup
