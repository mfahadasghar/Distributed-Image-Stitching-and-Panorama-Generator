import cv2
import numpy as np
from multiprocessing import Pool, Manager, cpu_count
from typing import List, Tuple, Optional, Dict, Any
import time
import os


class DistributedImageStitcher:
    """
    Distributed Image Stitching system using parallel processing
    for feature detection and matching
    """

    def __init__(self, feature_detector='SIFT', progress_callback=None):
        """
        Initialize the image stitcher

        Args:
            feature_detector: Type of feature detector (SIFT, ORB, AKAZE)
            progress_callback: Callback function for progress updates
        """
        self.feature_detector = feature_detector
        self.progress_callback = progress_callback
        self.min_match_count = 10

        # Initialize feature detector
        if feature_detector == 'SIFT':
            self.detector = cv2.SIFT_create()
        elif feature_detector == 'ORB':
            self.detector = cv2.ORB_create(nfeatures=2000)
        elif feature_detector == 'AKAZE':
            self.detector = cv2.AKAZE_create()
        else:
            raise ValueError(f"Unknown feature detector: {feature_detector}")

    def _update_progress(self, stage: str, percent: float, message: str = ""):
        """Update progress through callback"""
        if self.progress_callback:
            self.progress_callback({
                'stage': stage,
                'percent': percent,
                'message': message
            })

    def load_images(self, image_paths: List[str]) -> List[np.ndarray]:
        """
        Load images from file paths

        Args:
            image_paths: List of image file paths

        Returns:
            List of loaded images
        """
        self._update_progress('loading', 0, 'Loading images...')
        images = []

        for i, path in enumerate(image_paths):
            img = cv2.imread(path)
            if img is None:
                raise ValueError(f"Failed to load image: {path}")
            images.append(img)

            progress = ((i + 1) / len(image_paths)) * 100
            self._update_progress('loading', progress, f'Loaded {i + 1}/{len(image_paths)} images')

        return images

    def detect_features_single(self, image: np.ndarray) -> Tuple[Any, Any]:
        """
        Detect keypoints and descriptors for a single image

        Args:
            image: Input image

        Returns:
            Tuple of (keypoints, descriptors)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        keypoints, descriptors = self.detector.detectAndCompute(gray, None)
        return keypoints, descriptors

    def detect_features_parallel(self, images: List[np.ndarray]) -> List[Tuple[Any, Any]]:
        """
        Detect features in parallel across multiple images

        Args:
            images: List of input images

        Returns:
            List of (keypoints, descriptors) tuples
        """
        self._update_progress('features', 0, 'Detecting features in parallel...')

        # Use multiprocessing for parallel feature detection
        with Pool(processes=min(cpu_count(), len(images))) as pool:
            results = pool.map(self.detect_features_single, images)

        self._update_progress('features', 100, f'Features detected for {len(images)} images')
        return results

    def match_features(self, desc1: np.ndarray, desc2: np.ndarray) -> List[cv2.DMatch]:
        """
        Match features between two images

        Args:
            desc1: Descriptors from first image
            desc2: Descriptors from second image

        Returns:
            List of good matches
        """
        # Use BFMatcher for SIFT/AKAZE, or FLANN for better performance
        if self.feature_detector in ['SIFT', 'AKAZE']:
            bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
            matches = bf.knnMatch(desc1, desc2, k=2)
        else:
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            matches = bf.knnMatch(desc1, desc2, k=2)

        # Apply ratio test (Lowe's ratio test)
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)

        return good_matches

    def find_homography(self, kp1, kp2, matches) -> Optional[np.ndarray]:
        """
        Find homography matrix between two sets of keypoints

        Args:
            kp1: Keypoints from first image
            kp2: Keypoints from second image
            matches: List of matches

        Returns:
            Homography matrix or None
        """
        if len(matches) < self.min_match_count:
            return None

        # Extract matched keypoints
        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

        # Find homography using RANSAC
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        return H

    def warp_and_blend(self, img1: np.ndarray, img2: np.ndarray, H: np.ndarray) -> np.ndarray:
        """
        Warp and blend two images using homography

        Args:
            img1: First image (to be warped)
            img2: Second image (base)
            H: Homography matrix

        Returns:
            Stitched panorama
        """
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]

        # Get corners of first image
        corners1 = np.float32([[0, 0], [0, h1], [w1, h1], [w1, 0]]).reshape(-1, 1, 2)
        corners2 = np.float32([[0, 0], [0, h2], [w2, h2], [w2, 0]]).reshape(-1, 1, 2)

        # Transform corners of first image
        corners1_transformed = cv2.perspectiveTransform(corners1, H)

        # Get all corners
        all_corners = np.concatenate((corners2, corners1_transformed), axis=0)

        # Find bounding box
        [x_min, y_min] = np.int32(all_corners.min(axis=0).ravel() - 0.5)
        [x_max, y_max] = np.int32(all_corners.max(axis=0).ravel() + 0.5)

        # Translation matrix
        translation = np.array([[1, 0, -x_min],
                               [0, 1, -y_min],
                               [0, 0, 1]])

        # Warp first image
        output_size = (x_max - x_min, y_max - y_min)
        warped_img = cv2.warpPerspective(img1, translation.dot(H), output_size)

        # Create output image
        result = warped_img.copy()

        # Place second image
        result[-y_min:-y_min + h2, -x_min:-x_min + w2] = img2

        return result

    def stitch_images(self, image_paths: List[str]) -> Tuple[np.ndarray, Dict]:
        """
        Stitch multiple images into a panorama using distributed processing

        Args:
            image_paths: List of image file paths

        Returns:
            Tuple of (panorama image, statistics dict)
        """
        start_time = time.time()
        stats = {
            'num_images': len(image_paths),
            'feature_detector': self.feature_detector,
            'stages': {}
        }

        # Step 1: Load images
        images = self.load_images(image_paths)
        stats['stages']['loading'] = time.time() - start_time

        # Step 2: Detect features in parallel
        feature_start = time.time()
        features = self.detect_features_parallel(images)
        stats['stages']['feature_detection'] = time.time() - feature_start

        # Step 3: Sequential stitching with progress updates
        self._update_progress('stitching', 0, 'Starting image stitching...')

        result = images[0]
        result_kp, result_desc = features[0]

        for i in range(1, len(images)):
            stitch_start = time.time()

            # Get features for next image
            next_kp, next_desc = features[i]

            # Match features
            matches = self.match_features(result_desc, next_desc)
            match_msg = f'Found {len(matches)} matches between images'
            self._update_progress('stitching', (i / len(images)) * 50, match_msg)

            if len(matches) < self.min_match_count:
                raise ValueError(f"Not enough matches found between images ({len(matches)} < {self.min_match_count})")

            # Find homography
            H = self.find_homography(result_kp, next_kp, matches)

            if H is None:
                raise ValueError(f"Failed to find homography for image {i}")

            # Warp and blend
            result = self.warp_and_blend(images[i], result, H)

            # Update features for next iteration
            result_kp, result_desc = self.detect_features_single(result)

            progress = 50 + ((i / len(images)) * 50)
            self._update_progress('stitching', progress, f'Stitched {i + 1}/{len(images)} images')

        stats['total_time'] = time.time() - start_time
        self._update_progress('complete', 100, 'Panorama generation complete!')

        return result, stats

    def stitch_and_save(self, image_paths: List[str], output_path: str) -> Dict:
        """
        Stitch images and save the result

        Args:
            image_paths: List of image file paths
            output_path: Path to save the panorama

        Returns:
            Statistics dictionary
        """
        panorama, stats = self.stitch_images(image_paths)

        # Save the result
        cv2.imwrite(output_path, panorama)
        stats['output_path'] = output_path

        return stats
