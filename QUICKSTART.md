# Quick Start Guide - Run Locally

## Prerequisites
- Python 3.8 or higher installed on your machine
- pip (Python package manager)

## Steps to Run on Your Local Machine

### 1. Clone/Download the Repository

```bash
# If you have git
git clone https://github.com/mfahadasghar/Distributed-Image-Stitching-and-Panorama-Generator.git
cd Distributed-Image-Stitching-and-Panorama-Generator

# Or download the ZIP file from GitHub and extract it
```

### 2. Install Dependencies

**On Windows:**
```bash
# Run the batch file
run.bat

# Or manually:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**On macOS/Linux:**
```bash
# Run the shell script
chmod +x run.sh
./run.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### 3. Access the Application

Open your web browser and go to:
```
http://localhost:5000
```

### 4. Upload and Test

1. Prepare 2-4 images with overlapping content
2. Drag and drop them into the upload area
3. Select a feature detector (SIFT recommended)
4. Click "Start Stitching"
5. Watch the real-time progress!

## Troubleshooting

**Port already in use?**
```bash
# Change the port in app.py (last line)
socketio.run(app, debug=True, host='0.0.0.0', port=8080)
# Then access at http://localhost:8080
```

**Dependencies not installing?**
```bash
# Try upgrading pip first
pip install --upgrade pip
pip install -r requirements.txt
```

**OpenCV issues on macOS?**
```bash
# Install using conda instead
conda install -c conda-forge opencv
```

## Quick Test

To verify it's working:
```bash
curl http://localhost:5000
# Should return HTML content
```

## Need Help?

- Check README.md for detailed documentation
- Check USAGE.md for usage examples
- Check ARCHITECTURE.md for technical details
