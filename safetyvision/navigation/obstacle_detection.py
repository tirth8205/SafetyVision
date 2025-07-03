"""
Computer vision-based obstacle detection for nuclear facility navigation
"""

import cv2
import numpy as np
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import threading
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class Obstacle:
    """Detected obstacle information"""
    id: str
    position: Tuple[float, float]  # (x, y) in world coordinates
    size: Tuple[float, float]      # (width, height) in meters
    confidence: float
    obstacle_type: str             # 'static', 'dynamic', 'person', 'equipment'
    distance: float                # Distance from robot in meters
    velocity: Optional[Tuple[float, float]] = None  # (vx, vy) for dynamic obstacles
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class DetectionRegion:
    """Region of interest for obstacle detection"""
    x: int
    y: int
    width: int
    height: int
    weight: float = 1.0  # Importance weight for this region


class ObstacleDetector:
    """
    Multi-modal obstacle detection system for nuclear facility robots
    
    Combines computer vision, depth sensing, and safety constraints
    to detect and track obstacles in the robot's environment.
    """
    
    def __init__(self, camera_params: Optional[Dict] = None):
        self.camera_params = camera_params or {
            'fx': 525.0,  # Focal length x
            'fy': 525.0,  # Focal length y
            'cx': 320.0,  # Principal point x
            'cy': 240.0,  # Principal point y
            'baseline': 0.075,  # Stereo baseline in meters
        }
        
        # Detection parameters
        self.min_obstacle_size = (0.1, 0.1)  # Minimum size in meters
        self.max_detection_distance = 10.0    # Maximum detection range in meters
        self.confidence_threshold = 0.5       # Minimum confidence for detection
        
        # Tracking
        self.tracked_obstacles = {}  # id -> Obstacle
        self.next_obstacle_id = 0
        self.max_tracking_age = 5.0  # Remove obstacles not seen for 5 seconds
        
        # Detection regions (prioritize different areas)
        self.detection_regions = [
            DetectionRegion(0, 240, 640, 240, weight=2.0),    # Ground level - high priority
            DetectionRegion(160, 120, 320, 240, weight=1.5),  # Center - medium priority
            DetectionRegion(0, 0, 640, 120, weight=0.5),      # Upper area - low priority
        ]
        
        # Background subtractor for motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
        
        # Safety zones
        self.safety_zones = {
            'critical': 0.5,  # meters - immediate stop
            'warning': 1.5,   # meters - slow down
            'monitor': 3.0,   # meters - track only
        }
        
        logger.info("Obstacle detector initialized")
    
    async def detect_obstacles(self, 
                             rgb_image: np.ndarray,
                             depth_image: Optional[np.ndarray] = None,
                             robot_position: Optional[Tuple[float, float]] = None) -> List[Obstacle]:
        """
        Detect obstacles in the current frame
        
        Args:
            rgb_image: RGB camera image
            depth_image: Optional depth image from stereo/depth camera
            robot_position: Current robot position (x, y)
            
        Returns:
            List of detected obstacles
        """
        obstacles = []
        
        # Detect static obstacles using computer vision
        static_obstacles = await self._detect_static_obstacles(rgb_image, depth_image)
        obstacles.extend(static_obstacles)
        
        # Detect dynamic obstacles using motion detection
        dynamic_obstacles = await self._detect_dynamic_obstacles(rgb_image, depth_image)
        obstacles.extend(dynamic_obstacles)
        
        # Detect people using specialized detection
        people_obstacles = await self._detect_people(rgb_image, depth_image)
        obstacles.extend(people_obstacles)
        
        # Update tracking
        tracked_obstacles = self._update_tracking(obstacles)
        
        # Filter by safety zones and confidence
        filtered_obstacles = self._filter_obstacles(tracked_obstacles)
        
        return filtered_obstacles
    
    async def _detect_static_obstacles(self, rgb_image: np.ndarray, depth_image: Optional[np.ndarray]) -> List[Obstacle]:
        """Detect static obstacles using edge detection and contours"""
        obstacles = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Filter small contours
                area = cv2.contourArea(contour)
                if area < 500:  # Minimum pixel area
                    continue
                
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calculate center point
                center_x = x + w // 2
                center_y = y + h // 2
                
                # Estimate distance and world coordinates
                if depth_image is not None:
                    distance = self._get_depth_at_point(depth_image, center_x, center_y)
                else:
                    # Estimate distance from object size (rough approximation)
                    distance = max(1.0, 1000.0 / max(w, h))  # Simple heuristic
                
                if distance > self.max_detection_distance:
                    continue
                
                # Convert to world coordinates
                world_pos = self._pixel_to_world(center_x, center_y, distance)
                world_size = self._pixel_size_to_world(w, h, distance)
                
                # Check minimum size constraint
                if world_size[0] < self.min_obstacle_size[0] or world_size[1] < self.min_obstacle_size[1]:
                    continue
                
                # Calculate confidence based on contour properties
                confidence = min(0.9, area / 5000.0)  # Higher area = higher confidence
                
                obstacle = Obstacle(
                    id=f"static_{self.next_obstacle_id}",
                    position=world_pos,
                    size=world_size,
                    confidence=confidence,
                    obstacle_type='static',
                    distance=distance
                )
                
                obstacles.append(obstacle)
                self.next_obstacle_id += 1
                
        except Exception as e:
            logger.error(f"Error in static obstacle detection: {e}")
        
        return obstacles
    
    async def _detect_dynamic_obstacles(self, rgb_image: np.ndarray, depth_image: Optional[np.ndarray]) -> List[Obstacle]:
        """Detect moving obstacles using background subtraction"""
        obstacles = []
        
        try:
            # Apply background subtraction
            fg_mask = self.bg_subtractor.apply(rgb_image)
            
            # Remove shadows
            fg_mask[fg_mask == 127] = 0  # Shadow pixels
            
            # Morphological operations to clean up the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours of moving objects
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 200:  # Minimum area for moving objects
                    continue
                
                x, y, w, h = cv2.boundingRect(contour)
                center_x = x + w // 2
                center_y = y + h // 2
                
                # Estimate distance
                if depth_image is not None:
                    distance = self._get_depth_at_point(depth_image, center_x, center_y)
                else:
                    distance = max(1.0, 800.0 / max(w, h))
                
                if distance > self.max_detection_distance:
                    continue
                
                world_pos = self._pixel_to_world(center_x, center_y, distance)
                world_size = self._pixel_size_to_world(w, h, distance)
                
                # Estimate velocity (simplified - would need proper tracking)
                velocity = (0.0, 0.0)  # TODO: Implement proper velocity estimation
                
                confidence = min(0.8, area / 2000.0)
                
                obstacle = Obstacle(
                    id=f"dynamic_{self.next_obstacle_id}",
                    position=world_pos,
                    size=world_size,
                    confidence=confidence,
                    obstacle_type='dynamic',
                    distance=distance,
                    velocity=velocity
                )
                
                obstacles.append(obstacle)
                self.next_obstacle_id += 1
                
        except Exception as e:
            logger.error(f"Error in dynamic obstacle detection: {e}")
        
        return obstacles
    
    async def _detect_people(self, rgb_image: np.ndarray, depth_image: Optional[np.ndarray]) -> List[Obstacle]:
        """Detect people using HOG detector"""
        obstacles = []
        
        try:
            # Initialize HOG descriptor for people detection
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            
            # Detect people
            people, weights = hog.detectMultiScale(rgb_image, winStride=(8, 8), padding=(32, 32), scale=1.05)
            
            for i, (x, y, w, h) in enumerate(people):
                center_x = x + w // 2
                center_y = y + h // 2
                
                # Estimate distance
                if depth_image is not None:
                    distance = self._get_depth_at_point(depth_image, center_x, center_y)
                else:
                    # Estimate based on typical person height
                    distance = max(1.0, (1.7 * self.camera_params['fy']) / h)
                
                if distance > self.max_detection_distance:
                    continue
                
                world_pos = self._pixel_to_world(center_x, center_y, distance)
                world_size = self._pixel_size_to_world(w, h, distance)
                
                # People detection has higher priority
                confidence = min(0.95, weights[i] * 0.8)
                
                obstacle = Obstacle(
                    id=f"person_{self.next_obstacle_id}",
                    position=world_pos,
                    size=world_size,
                    confidence=confidence,
                    obstacle_type='person',
                    distance=distance
                )
                
                obstacles.append(obstacle)
                self.next_obstacle_id += 1
                
        except Exception as e:
            logger.error(f"Error in people detection: {e}")
        
        return obstacles
    
    def _get_depth_at_point(self, depth_image: np.ndarray, x: int, y: int) -> float:
        """Get depth value at specific pixel coordinates"""
        if 0 <= x < depth_image.shape[1] and 0 <= y < depth_image.shape[0]:
            # Sample a small region around the point for more robust depth
            region = depth_image[max(0, y-2):min(depth_image.shape[0], y+3),
                                max(0, x-2):min(depth_image.shape[1], x+3)]
            
            # Use median to handle noise
            valid_depths = region[region > 0]
            if len(valid_depths) > 0:
                return float(np.median(valid_depths)) / 1000.0  # Convert mm to meters
        
        return 5.0  # Default distance if no valid depth
    
    def _pixel_to_world(self, pixel_x: int, pixel_y: int, distance: float) -> Tuple[float, float]:
        """Convert pixel coordinates to world coordinates"""
        # Simple pinhole camera model
        world_x = (pixel_x - self.camera_params['cx']) * distance / self.camera_params['fx']
        world_y = (pixel_y - self.camera_params['cy']) * distance / self.camera_params['fy']
        return (world_x, world_y)
    
    def _pixel_size_to_world(self, pixel_width: int, pixel_height: int, distance: float) -> Tuple[float, float]:
        """Convert pixel size to world size"""
        world_width = pixel_width * distance / self.camera_params['fx']
        world_height = pixel_height * distance / self.camera_params['fy']
        return (world_width, world_height)
    
    def _update_tracking(self, new_obstacles: List[Obstacle]) -> List[Obstacle]:
        """Update obstacle tracking with temporal consistency"""
        current_time = datetime.now()
        
        # Remove old obstacles
        self.tracked_obstacles = {
            obs_id: obs for obs_id, obs in self.tracked_obstacles.items()
            if (current_time - obs.timestamp).total_seconds() < self.max_tracking_age
        }
        
        # Simple tracking: match new obstacles to existing ones by distance
        matched_obstacles = []
        
        for new_obs in new_obstacles:
            best_match = None
            best_distance = float('inf')
            
            for obs_id, tracked_obs in self.tracked_obstacles.items():
                # Skip if already matched
                if obs_id in [obs.id for obs in matched_obstacles]:
                    continue
                
                # Calculate distance between obstacles
                dx = new_obs.position[0] - tracked_obs.position[0]
                dy = new_obs.position[1] - tracked_obs.position[1]
                distance = np.sqrt(dx*dx + dy*dy)
                
                # Must be similar type and within reasonable distance
                if (new_obs.obstacle_type == tracked_obs.obstacle_type and 
                    distance < 1.0 and distance < best_distance):
                    best_match = obs_id
                    best_distance = distance
            
            if best_match:
                # Update existing obstacle
                tracked_obs = self.tracked_obstacles[best_match]
                tracked_obs.position = new_obs.position
                tracked_obs.size = new_obs.size
                tracked_obs.confidence = max(tracked_obs.confidence, new_obs.confidence)
                tracked_obs.distance = new_obs.distance
                tracked_obs.timestamp = current_time
                
                # Update velocity for dynamic obstacles
                if new_obs.obstacle_type == 'dynamic':
                    time_diff = (current_time - tracked_obs.timestamp).total_seconds()
                    if time_diff > 0:
                        vx = (new_obs.position[0] - tracked_obs.position[0]) / time_diff
                        vy = (new_obs.position[1] - tracked_obs.position[1]) / time_diff
                        tracked_obs.velocity = (vx, vy)
                
                matched_obstacles.append(tracked_obs)
            else:
                # New obstacle
                self.tracked_obstacles[new_obs.id] = new_obs
                matched_obstacles.append(new_obs)
        
        return matched_obstacles
    
    def _filter_obstacles(self, obstacles: List[Obstacle]) -> List[Obstacle]:
        """Filter obstacles based on confidence and safety constraints"""
        filtered = []
        
        for obstacle in obstacles:
            # Confidence filter
            if obstacle.confidence < self.confidence_threshold:
                continue
            
            # Distance filter
            if obstacle.distance > self.max_detection_distance:
                continue
            
            # Size filter
            if (obstacle.size[0] < self.min_obstacle_size[0] or 
                obstacle.size[1] < self.min_obstacle_size[1]):
                continue
            
            filtered.append(obstacle)
        
        return filtered
    
    def get_safety_zones_status(self, obstacles: List[Obstacle]) -> Dict[str, List[Obstacle]]:
        """Categorize obstacles by safety zones"""
        zones = {zone: [] for zone in self.safety_zones.keys()}
        
        for obstacle in obstacles:
            for zone, max_distance in self.safety_zones.items():
                if obstacle.distance <= max_distance:
                    zones[zone].append(obstacle)
                    break  # Place in most restrictive zone only
        
        return zones
    
    def visualize_detections(self, image: np.ndarray, obstacles: List[Obstacle]) -> np.ndarray:
        """Visualize detected obstacles on image"""
        vis_image = image.copy()
        
        for obstacle in obstacles:
            # Convert world coordinates back to pixels (approximate)
            pixel_x = int(obstacle.position[0] * self.camera_params['fx'] / obstacle.distance + self.camera_params['cx'])
            pixel_y = int(obstacle.position[1] * self.camera_params['fy'] / obstacle.distance + self.camera_params['cy'])
            
            # Choose color based on obstacle type and distance
            if obstacle.obstacle_type == 'person':
                color = (0, 0, 255)  # Red for people
            elif obstacle.distance <= self.safety_zones['critical']:
                color = (255, 0, 0)  # Blue for critical
            elif obstacle.distance <= self.safety_zones['warning']:
                color = (0, 255, 255)  # Yellow for warning
            else:
                color = (0, 255, 0)  # Green for monitor
            
            # Draw bounding box
            width = int(obstacle.size[0] * self.camera_params['fx'] / obstacle.distance)
            height = int(obstacle.size[1] * self.camera_params['fy'] / obstacle.distance)
            
            cv2.rectangle(vis_image, 
                         (pixel_x - width//2, pixel_y - height//2),
                         (pixel_x + width//2, pixel_y + height//2),
                         color, 2)
            
            # Add label
            label = f"{obstacle.obstacle_type} ({obstacle.distance:.1f}m)"
            cv2.putText(vis_image, label, 
                       (pixel_x - width//2, pixel_y - height//2 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return vis_image