# Usage Guide

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or use the startup script
./run.sh           # Linux/Mac
run.bat            # Windows
```

### 2. Run the Application

```bash
python app.py
```

Open your browser at `http://127.0.0.1:5000`

## Detailed Usage

### Preparing Images

For best results:
- Use images with **30-50% overlap** between adjacent images
- Keep consistent lighting conditions
- Use the same camera/settings for all images
- Take images from left to right or top to bottom
- Minimum 2 images, recommended 3-6 images
- Higher resolution = better quality (but slower processing)

### Feature Detector Selection

#### SIFT (Scale-Invariant Feature Transform)
- **Best for**: High-quality panoramas
- **Speed**: Slower
- **Quality**: Excellent
- **Use when**: Quality is priority

#### ORB (Oriented FAST and Rotated BRIEF)
- **Best for**: Quick results
- **Speed**: Fast
- **Quality**: Good
- **Use when**: Speed is priority

#### AKAZE (Accelerated-KAZE)
- **Best for**: Balanced results
- **Speed**: Medium
- **Quality**: Very good
- **Use when**: Balance between speed and quality

### Understanding Progress Stages

#### Stage 1: Loading Images (5-10% of total time)
- Reads images from disk
- Validates image formats
- Prepares data structures

#### Stage 2: Feature Detection (30-40% of total time)
- **Parallel Processing**: Uses all CPU cores
- Detects keypoints in each image
- Computes feature descriptors
- **Why it's fast**: Multiple images processed simultaneously

#### Stage 3: Stitching (50-60% of total time)
- Matches features between images
- Estimates homography transformations
- Warps and blends images
- Creates final panorama

#### Stage 4: Complete
- Saves final result
- Displays statistics

## API Usage

### Upload Images
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

Response:
```json
{
  "job_id": "abc-123-def",
  "num_files": 3,
  "message": "Files uploaded successfully"
}
```

### Start Stitching
```bash
curl -X POST http://localhost:5000/api/stitch/abc-123-def \
  -H "Content-Type: application/json" \
  -d '{"feature_detector": "SIFT"}'
```

### Check Status
```bash
curl http://localhost:5000/api/job/abc-123-def
```

### Download Result
```bash
curl http://localhost:5000/api/result/panorama_abc-123-def.jpg \
  --output panorama.jpg
```

## Advanced Configuration

### Adjusting Parallel Workers

Edit `config.py`:
```python
MAX_WORKERS = 8  # Use 8 CPU cores
```

### Changing Match Threshold

```python
MIN_MATCH_COUNT = 15  # Require more matches (more strict)
```

### Adjusting RANSAC Threshold

```python
RANSAC_THRESHOLD = 3.0  # Lower = more strict
```

## Troubleshooting

### Problem: "Not enough matches found"

**Causes:**
- Insufficient overlap between images
- Different lighting conditions
- Motion blur

**Solutions:**
1. Increase overlap between images (50%+)
2. Retake images with consistent settings
3. Lower `MIN_MATCH_COUNT` in config
4. Try different feature detector

### Problem: Distorted panorama

**Causes:**
- Images not in correct order
- Too much parallax
- Moving objects

**Solutions:**
1. Ensure images are in sequence
2. Keep camera rotation point consistent
3. Avoid moving objects in scene
4. Use tripod for better results

### Problem: Slow processing

**Solutions:**
1. Use ORB feature detector
2. Reduce image resolution
3. Close other applications
4. Increase `MAX_WORKERS` for more parallel processing

### Problem: Out of memory

**Solutions:**
1. Reduce image resolution
2. Process fewer images at once
3. Close other applications
4. Increase system RAM

## Performance Optimization

### Image Resolution
- **4K images**: 5-10 seconds per image
- **1080p images**: 1-2 seconds per image
- **720p images**: <1 second per image

### Parallel Speedup
- **2 cores**: ~1.8x faster
- **4 cores**: ~3.5x faster
- **8 cores**: ~6x faster
- **16 cores**: ~9x faster

### Best Practices
1. Use JPEG for faster loading
2. Keep image count between 3-6
3. Use consistent resolution
4. Enable parallel processing
5. Use SSD for storage

## Example Workflows

### Workflow 1: Quick Test
1. Use 3 images at 720p
2. Select ORB detector
3. Process time: ~5 seconds

### Workflow 2: High Quality
1. Use 5 images at 4K
2. Select SIFT detector
3. Process time: ~30 seconds

### Workflow 3: Balanced
1. Use 4 images at 1080p
2. Select AKAZE detector
3. Process time: ~12 seconds

## Command Line Usage

You can also use the stitcher programmatically:

```python
from image_stitcher import DistributedImageStitcher

# Create stitcher
stitcher = DistributedImageStitcher(feature_detector='SIFT')

# Stitch images
image_paths = ['img1.jpg', 'img2.jpg', 'img3.jpg']
panorama, stats = stitcher.stitch_images(image_paths)

# Save result
import cv2
cv2.imwrite('output.jpg', panorama)

print(f"Processing time: {stats['total_time']:.2f}s")
```

## Getting Help

- Check [README.md](README.md) for overview
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Open GitHub issues for bugs
- Check OpenCV documentation for algorithms

## Tips for Best Results

1. **Camera Setup**
   - Use tripod or keep rotation point steady
   - Lock exposure and white balance
   - Use manual focus

2. **Scene Selection**
   - Choose scenes with texture (avoid blank walls)
   - Avoid moving objects
   - Good lighting helps

3. **Capture Technique**
   - Rotate camera, don't translate
   - Maintain 30-50% overlap
   - Keep horizon level
   - Capture in sequence

4. **Processing**
   - Start with fewer images to test
   - Choose appropriate feature detector
   - Monitor progress stages
   - Check statistics for insights

## Common Use Cases

### 1. Landscape Panoramas
- Use SIFT for quality
- 3-5 images typical
- Wide overlap (40%+)

### 2. Indoor 360° Views
- Use AKAZE for balance
- 6-8 images for full circle
- Ensure consistent overlap

### 3. Architectural Photography
- Use SIFT for detail
- Keep parallel to building
- Multiple rows if needed

### 4. Group Photos
- Use ORB for speed
- 2-3 images typical
- Keep people still

## FAQ

**Q: Can I use different cameras?**
A: Not recommended. Use same camera/settings for consistency.

**Q: How many images can I stitch?**
A: Technically unlimited, but 3-6 images is optimal for performance.

**Q: Does it work with RAW files?**
A: Convert to JPEG first. RAW processing is not supported.

**Q: Can I stitch vertically?**
A: Yes, the algorithm works in any direction.

**Q: What about 360° panoramas?**
A: Possible with 8+ images, but may need manual adjustment.

**Q: Does it work on video?**
A: Not directly. Extract frames first, then stitch.
