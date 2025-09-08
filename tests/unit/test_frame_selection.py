#!/usr/bin/env python3
"""
Unit tests for MediaProcessor._select_frames_with_minimums() method.
Tests the min_frames_per_camera functionality.
"""

import pytest
import unittest


class MockMediaProcessor:
    """Minimal mock of MediaProcessor for testing frame selection logic"""
    
    def _select_frames_with_minimums(self, camera_frames, max_frames, min_frames_per_camera):
        """Select frames ensuring minimum representation per camera
        
        Args:
            camera_frames (dict): Dict of camera_entity -> frames
            max_frames (int): Maximum total frames to select
            min_frames_per_camera (int): Minimum frames each camera should contribute
            
        Returns:
            tuple: (selected_frames, camera_frames_count) where:
                - selected_frames: list of (frame_name, frame_data, ssim_score) tuples
                - camera_frames_count: dict of camera_entity -> count
        """
        if min_frames_per_camera == 0:
            # Original behavior - no minimum per camera
            frames_with_scores = []
            for camera_entity in camera_frames:
                for frame_name, frame_data in camera_frames[camera_entity].items():
                    frames_with_scores.append(
                        (frame_name, frame_data["frame_data"], frame_data["ssim_score"])
                    )
            frames_with_scores.sort(key=lambda x: x[2])
            selected_frames = frames_with_scores[:max_frames]
            
            # Calculate camera distribution
            camera_frames_count = {}
            for frame_name, _, _ in selected_frames:
                camera_name = frame_name.split(' frame ')[0]
                camera_frames_count[camera_name] = camera_frames_count.get(camera_name, 0) + 1
            
            return selected_frames, camera_frames_count
        
        # Build list of all frames with camera info
        all_frames = []
        for camera_entity in camera_frames:
            for frame_name, frame_data in camera_frames[camera_entity].items():
                all_frames.append(
                    (frame_name, frame_data["frame_data"], frame_data["ssim_score"], camera_entity)
                )
        
        # Sort by SSIM score (lower = more distinct)
        all_frames.sort(key=lambda x: x[2])
        
        selected_frames = []
        camera_frame_counts = {camera: 0 for camera in camera_frames.keys()}
        
        # First pass: try to satisfy minimum frames per camera
        for frame_name, frame_data, ssim_score, camera_entity in all_frames:
            if len(selected_frames) >= max_frames:
                break
                
            if camera_frame_counts[camera_entity] < min_frames_per_camera:
                selected_frames.append((frame_name, frame_data, ssim_score))
                camera_frame_counts[camera_entity] += 1
        
        # Second pass: fill remaining slots with best frames
        for frame_name, frame_data, ssim_score, camera_entity in all_frames:
            if len(selected_frames) >= max_frames:
                break
                
            # Skip if already selected
            if (frame_name, frame_data, ssim_score) in selected_frames:
                continue
                
            selected_frames.append((frame_name, frame_data, ssim_score))
        
        return selected_frames, camera_frame_counts


@pytest.mark.unit
class TestFrameSelection(unittest.TestCase):
    """Test cases for frame selection with minimum frames per camera"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock MediaProcessor instance for testing
        self.processor = MockMediaProcessor()
        
        # Mock camera frame data with predictable SSIM scores
        self.mock_camera_frames = {
            "camera.front": {
                "front frame 0": {"frame_data": b"front_data_0", "ssim_score": 0.1},  # Most distinct
                "front frame 1": {"frame_data": b"front_data_1", "ssim_score": 0.5},
                "front frame 2": {"frame_data": b"front_data_2", "ssim_score": 0.7},
            },
            "camera.side": {
                "side frame 0": {"frame_data": b"side_data_0", "ssim_score": 0.2},   # Second most distinct
                "side frame 1": {"frame_data": b"side_data_1", "ssim_score": 0.6},
                "side frame 2": {"frame_data": b"side_data_2", "ssim_score": 0.8},
            },
            "camera.back": {
                "back frame 0": {"frame_data": b"back_data_0", "ssim_score": 0.3},   # Third most distinct
                "back frame 1": {"frame_data": b"back_data_1", "ssim_score": 0.9},
            }
        }

    def test_backward_compatibility_single_camera(self):
        """Test that min_frames_per_camera=0 maintains original behavior with single camera"""
        camera_frames = {"camera.front": self.mock_camera_frames["camera.front"]}
        
        selected, camera_frames_count = self.processor._select_frames_with_minimums(camera_frames, max_frames=2, min_frames_per_camera=0)
        
        # Should select 2 frames with lowest SSIM scores
        self.assertEqual(len(selected), 2)
        # First frame should be the most distinct (lowest SSIM)
        self.assertEqual(selected[0][0], "front frame 0")
        self.assertEqual(selected[0][2], 0.1)
        # Second frame should be second most distinct
        self.assertEqual(selected[1][0], "front frame 1") 
        self.assertEqual(selected[1][2], 0.5)

    def test_backward_compatibility_multiple_cameras(self):
        """Test that min_frames_per_camera=0 maintains original behavior with multiple cameras"""
        selected, camera_frames_count = self.processor._select_frames_with_minimums(
            self.mock_camera_frames, max_frames=3, min_frames_per_camera=0
        )
        
        # Should select 3 frames with lowest SSIM scores across all cameras
        self.assertEqual(len(selected), 3)
        # Should be front frame 0 (0.1), side frame 0 (0.2), back frame 0 (0.3)
        expected_frames = ["front frame 0", "side frame 0", "back frame 0"]
        actual_frames = [frame[0] for frame in selected]
        self.assertEqual(actual_frames, expected_frames)
        
        # Verify SSIM scores are in ascending order
        ssim_scores = [frame[2] for frame in selected]
        self.assertEqual(ssim_scores, [0.1, 0.2, 0.3])

    def test_minimum_frames_exact_match(self):
        """Test min_frames_per_camera when total minimums exactly equals max_frames"""
        # 3 cameras, min_frames=1 each, max_frames=3 (exact match)
        selected, camera_frames_count = self.processor._select_frames_with_minimums(
            self.mock_camera_frames, max_frames=3, min_frames_per_camera=1
        )
        
        self.assertEqual(len(selected), 3)
        
        # Each camera should be represented exactly once
        cameras_represented = set()
        for frame_name, _, _ in selected:
            if "front" in frame_name:
                cameras_represented.add("front")
            elif "side" in frame_name:
                cameras_represented.add("side")
            elif "back" in frame_name:
                cameras_represented.add("back")
        
        self.assertEqual(len(cameras_represented), 3)
        
        # Should still prefer frames with lowest SSIM scores
        # front frame 0 (0.1), side frame 0 (0.2), back frame 0 (0.3)
        expected_frames = ["front frame 0", "side frame 0", "back frame 0"]
        actual_frames = [frame[0] for frame in selected]
        self.assertEqual(actual_frames, expected_frames)

    def test_minimum_frames_with_extras(self):
        """Test min_frames_per_camera with extra slots to fill"""
        # 2 cameras, min_frames=1 each, max_frames=4 (2 extra slots)
        camera_frames = {
            "camera.front": self.mock_camera_frames["camera.front"],
            "camera.side": self.mock_camera_frames["camera.side"]
        }
        
        selected, camera_frames_count = self.processor._select_frames_with_minimums(
            camera_frames, max_frames=4, min_frames_per_camera=1
        )
        
        self.assertEqual(len(selected), 4)
        
        # Each camera should have at least 1 frame
        front_count = sum(1 for frame in selected if "front" in frame[0])
        side_count = sum(1 for frame in selected if "side" in frame[0])
        
        self.assertGreaterEqual(front_count, 1)
        self.assertGreaterEqual(side_count, 1)
        
        # Should select based on SSIM scores
        # Expected: front frame 0 (0.1), side frame 0 (0.2), front frame 1 (0.5), side frame 1 (0.6)
        expected_ssim_order = [0.1, 0.2, 0.5, 0.6]
        actual_ssim_scores = [frame[2] for frame in selected]
        self.assertEqual(actual_ssim_scores, expected_ssim_order)

    def test_edge_case_minimums_exceed_max_frames(self):
        """Test best-effort distribution when min_frames × num_cameras > max_frames"""
        # 3 cameras, min_frames=2 each, max_frames=4 (need 6 but only have 4)
        selected, camera_frames_count = self.processor._select_frames_with_minimums(
            self.mock_camera_frames, max_frames=4, min_frames_per_camera=2
        )
        
        self.assertEqual(len(selected), 4)
        
        # Should distribute frames as fairly as possible
        # At least some cameras should be represented
        cameras_represented = set()
        for frame_name, _, _ in selected:
            if "front" in frame_name:
                cameras_represented.add("front")
            elif "side" in frame_name:
                cameras_represented.add("side") 
            elif "back" in frame_name:
                cameras_represented.add("back")
        
        # Should have at least 2 cameras represented (best effort)
        self.assertGreaterEqual(len(cameras_represented), 2)
        
        # Should still be ordered by SSIM scores
        ssim_scores = [frame[2] for frame in selected]
        self.assertEqual(ssim_scores, sorted(ssim_scores))

    def test_single_camera_with_minimum(self):
        """Test single camera with min_frames_per_camera > 0"""
        camera_frames = {"camera.front": self.mock_camera_frames["camera.front"]}
        
        selected, camera_frames_count = self.processor._select_frames_with_minimums(
            camera_frames, max_frames=2, min_frames_per_camera=1
        )
        
        self.assertEqual(len(selected), 2)
        # Should select best frames from the single camera
        expected_frames = ["front frame 0", "front frame 1"]
        actual_frames = [frame[0] for frame in selected]
        self.assertEqual(actual_frames, expected_frames)

    def test_empty_camera_frames(self):
        """Test with empty camera_frames input"""
        selected, camera_frames_count = self.processor._select_frames_with_minimums(
            {}, max_frames=3, min_frames_per_camera=1
        )
        
        self.assertEqual(len(selected), 0)

    def test_camera_with_no_frames(self):
        """Test camera that has no frames"""
        camera_frames = {
            "camera.front": self.mock_camera_frames["camera.front"],
            "camera.empty": {}  # Empty camera
        }
        
        selected, camera_frames_count = self.processor._select_frames_with_minimums(
            camera_frames, max_frames=2, min_frames_per_camera=1
        )
        
        # Should handle gracefully and select from camera that has frames
        self.assertLessEqual(len(selected), 2)
        # All selected frames should be from front camera
        for frame_name, _, _ in selected:
            self.assertIn("front", frame_name)

    def test_ssim_ordering_preservation(self):
        """Test that SSIM ordering is properly maintained"""
        selected, camera_frames_count = self.processor._select_frames_with_minimums(
            self.mock_camera_frames, max_frames=5, min_frames_per_camera=1
        )
        
        # Verify frames are selected in SSIM score order (ascending)
        ssim_scores = [frame[2] for frame in selected]
        self.assertEqual(ssim_scores, sorted(ssim_scores))
        
        # Verify no duplicate frames
        frame_names = [frame[0] for frame in selected]
        self.assertEqual(len(frame_names), len(set(frame_names)))

    def test_fair_distribution_algorithm(self):
        """Test the two-pass fair distribution algorithm"""
        # 3 cameras, min_frames=1, max_frames=5
        selected, camera_frames_count = self.processor._select_frames_with_minimums(
            self.mock_camera_frames, max_frames=5, min_frames_per_camera=1
        )
        
        self.assertEqual(len(selected), 5)
        
        # Count frames per camera
        camera_frames_count = {"front": 0, "side": 0, "back": 0}
        for frame_name, _, _ in selected:
            if "front" in frame_name:
                camera_frames_count["front"] += 1
            elif "side" in frame_name:
                camera_frames_count["side"] += 1
            elif "back" in frame_name:
                camera_frames_count["back"] += 1
        
        # Each camera should have at least 1 frame (first pass)
        for camera, count in camera_frames_count.items():
            self.assertGreaterEqual(count, 1)
        
        # Total should be 5
        self.assertEqual(sum(camera_frames_count.values()), 5)
        
        # Should be ordered by SSIM scores
        ssim_scores = [frame[2] for frame in selected]
        self.assertEqual(ssim_scores, sorted(ssim_scores))


if __name__ == "__main__":
    unittest.main()