"""
Visual perception system for nuclear facility monitoring
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class VisualHazard(Enum):
    """Types of visual hazards that can be detected"""
    RADIATION_WARNING = "radiation_warning"
    STRUCTURAL_DAMAGE = "structural_damage"
    EQUIPMENT_MALFUNCTION = "equipment_malfunction"
    UNAUTHORIZED_PERSONNEL = "unauthorized_personnel"
    FIRE_SMOKE = "fire_smoke"
    LIQUID_SPILL = "liquid_spill"
    BLOCKED_EXIT = "blocked_exit"


@dataclass
class VisualDetection:
    """Visual detection result"""
    hazard_type: VisualHazard
    confidence: float
    bounding_box: Tuple[int, int, int, int]  # (x, y, width, height)
    description: str
    timestamp: datetime
    severity: float  # 0-1, where 1 is most severe


class VisualPerceptionSystem:
    """
    Computer vision system for nuclear facility safety monitoring
    
    Detects visual hazards, equipment states, and safety conditions
    using advanced computer vision techniques.
    """
    
    def __init__(self):
        self.detections_history = []
        self.current_detections = []
        
        # Initialize detection models (in production, would load actual models)
        self._initialize_detectors()
        
        # Detection thresholds
        self.confidence_threshold = 0.6
        self.severity_threshold = 0.5
        
        logger.info("Visual perception system initialized")
    
    def _initialize_detectors(self):
        """Initialize computer vision detectors"""
        # Initialize various CV models
        self.cascade_classifiers = {}
        
        try:
            # Load pre-trained classifiers (if available)
            self.cascade_classifiers['face'] = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        except:
            logger.warning("Could not load face cascade classifier")
        
        # Color ranges for hazard detection (HSV)
        self.color_ranges = {
            'radiation_yellow': {
                'lower': np.array([20, 100, 100]),
                'upper': np.array([30, 255, 255])
            },
            'warning_red': {
                'lower': np.array([0, 120, 70]),
                'upper': np.array([10, 255, 255])
            },
            'fire_orange': {
                'lower': np.array([5, 50, 50]),
                'upper': np.array([15, 255, 255])
            }
        }
    
    async def analyze_frame(self, image: np.ndarray) -> List[VisualDetection]:
        """
        Analyze a single frame for visual hazards
        
        Args:
            image: Input image in BGR format
            
        Returns:
            List of detected visual hazards
        """
        detections = []
        
        # Run different detection algorithms
        detections.extend(await self._detect_radiation_symbols(image))
        detections.extend(await self._detect_structural_issues(image))
        detections.extend(await self._detect_equipment_status(image))
        detections.extend(await self._detect_personnel(image))
        detections.extend(await self._detect_fire_smoke(image))
        detections.extend(await self._detect_spills(image))
        
        # Filter by confidence and severity
        filtered_detections = [
            det for det in detections 
            if det.confidence >= self.confidence_threshold
        ]
        
        self.current_detections = filtered_detections
        self.detections_history.extend(filtered_detections)
        
        return filtered_detections
    
    async def _detect_radiation_symbols(self, image: np.ndarray) -> List[VisualDetection]:
        """Detect radiation warning symbols and signs"""
        detections = []
        
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Detect yellow radiation warning colors
            yellow_mask = cv2.inRange(
                hsv, 
                self.color_ranges['radiation_yellow']['lower'],
                self.color_ranges['radiation_yellow']['upper']
            )
            
            # Find contours of yellow areas
            contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum area for radiation symbol
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Check aspect ratio (radiation symbols are often circular/square)
                    aspect_ratio = w / h
                    if 0.7 <= aspect_ratio <= 1.3:
                        confidence = min(0.9, area / 5000.0)
                        
                        detection = VisualDetection(
                            hazard_type=VisualHazard.RADIATION_WARNING,
                            confidence=confidence,
                            bounding_box=(x, y, w, h),
                            description="Radiation warning symbol detected",
                            timestamp=datetime.now(),
                            severity=0.8
                        )
                        detections.append(detection)
        
        except Exception as e:
            logger.error(f"Error in radiation symbol detection: {e}")
        
        return detections
    
    async def _detect_structural_issues(self, image: np.ndarray) -> List[VisualDetection]:
        """Detect structural damage like cracks, corrosion, etc."""
        detections = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Edge detection for cracks
            edges = cv2.Canny(gray, 50, 150)
            
            # Use HoughLines to detect linear cracks
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                  minLineLength=50, maxLineGap=10)
            
            if lines is not None:
                # Group nearby lines as potential cracks
                crack_groups = self._group_lines(lines)
                
                for group in crack_groups:
                    if len(group) >= 3:  # Multiple connected lines suggest a crack
                        # Calculate bounding box for the crack group
                        all_points = np.concatenate(group)
                        x_coords = all_points[:, [0, 2]].flatten()
                        y_coords = all_points[:, [1, 3]].flatten()
                        
                        x, w = int(np.min(x_coords)), int(np.max(x_coords) - np.min(x_coords))
                        y, h = int(np.min(y_coords)), int(np.max(y_coords) - np.min(y_coords))
                        
                        confidence = min(0.8, len(group) / 10.0)
                        
                        detection = VisualDetection(
                            hazard_type=VisualHazard.STRUCTURAL_DAMAGE,
                            confidence=confidence,
                            bounding_box=(x, y, w, h),
                            description=f"Potential structural crack detected ({len(group)} segments)",
                            timestamp=datetime.now(),
                            severity=0.7
                        )
                        detections.append(detection)
            
            # Detect corrosion using color analysis
            corrosion_detections = await self._detect_corrosion(image)
            detections.extend(corrosion_detections)
        
        except Exception as e:
            logger.error(f"Error in structural damage detection: {e}")
        
        return detections
    
    async def _detect_corrosion(self, image: np.ndarray) -> List[VisualDetection]:
        """Detect rust/corrosion using color analysis"""
        detections = []
        
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Define rust color range (brownish-orange)
            rust_lower = np.array([10, 50, 20])
            rust_upper = np.array([20, 255, 200])
            
            rust_mask = cv2.inRange(hsv, rust_lower, rust_upper)
            
            # Morphological operations to clean up
            kernel = np.ones((5, 5), np.uint8)
            rust_mask = cv2.morphologyEx(rust_mask, cv2.MORPH_CLOSE, kernel)
            
            contours, _ = cv2.findContours(rust_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Significant corrosion area
                    x, y, w, h = cv2.boundingRect(contour)
                    confidence = min(0.7, area / 10000.0)
                    
                    detection = VisualDetection(
                        hazard_type=VisualHazard.STRUCTURAL_DAMAGE,
                        confidence=confidence,
                        bounding_box=(x, y, w, h),
                        description="Potential corrosion/rust detected",
                        timestamp=datetime.now(),
                        severity=0.5
                    )
                    detections.append(detection)
        
        except Exception as e:
            logger.error(f"Error in corrosion detection: {e}")
        
        return detections
    
    async def _detect_equipment_status(self, image: np.ndarray) -> List[VisualDetection]:
        """Detect equipment status indicators (lights, gauges, etc.)"""
        detections = []
        
        try:
            # Detect red warning lights
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            red_mask = cv2.inRange(
                hsv,
                self.color_ranges['warning_red']['lower'],
                self.color_ranges['warning_red']['upper']
            )
            
            # Find circular red objects (warning lights)
            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 2000:  # Typical warning light size
                    # Check if roughly circular
                    perimeter = cv2.arcLength(contour, True)
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    
                    if circularity > 0.7:  # Fairly circular
                        x, y, w, h = cv2.boundingRect(contour)
                        confidence = min(0.8, circularity)
                        
                        detection = VisualDetection(
                            hazard_type=VisualHazard.EQUIPMENT_MALFUNCTION,
                            confidence=confidence,
                            bounding_box=(x, y, w, h),
                            description="Warning light/indicator detected",
                            timestamp=datetime.now(),
                            severity=0.6
                        )
                        detections.append(detection)
        
        except Exception as e:
            logger.error(f"Error in equipment status detection: {e}")
        
        return detections
    
    async def _detect_personnel(self, image: np.ndarray) -> List[VisualDetection]:
        """Detect unauthorized personnel"""
        detections = []
        
        try:
            if 'face' in self.cascade_classifiers:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                faces = self.cascade_classifiers['face'].detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )
                
                for (x, y, w, h) in faces:
                    # In a real system, would check against authorized personnel database
                    confidence = 0.7  # Simplified confidence
                    
                    detection = VisualDetection(
                        hazard_type=VisualHazard.UNAUTHORIZED_PERSONNEL,
                        confidence=confidence,
                        bounding_box=(x, y, w, h),
                        description="Person detected - verify authorization",
                        timestamp=datetime.now(),
                        severity=0.8
                    )
                    detections.append(detection)
        
        except Exception as e:
            logger.error(f"Error in personnel detection: {e}")
        
        return detections
    
    async def _detect_fire_smoke(self, image: np.ndarray) -> List[VisualDetection]:
        """Detect fire and smoke"""
        detections = []
        
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Detect fire colors (orange/red)
            fire_mask = cv2.inRange(
                hsv,
                self.color_ranges['fire_orange']['lower'],
                self.color_ranges['fire_orange']['upper']
            )
            
            # Detect potential smoke (grayish areas with motion)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Simple smoke detection using brightness variations
            blurred = cv2.GaussianBlur(gray, (15, 15), 0)
            smoke_regions = cv2.threshold(blurred, 100, 255, cv2.THRESH_BINARY)[1]
            
            # Combine fire and smoke detections
            combined_mask = cv2.bitwise_or(fire_mask, smoke_regions)
            
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 2000:  # Significant fire/smoke area
                    x, y, w, h = cv2.boundingRect(contour)
                    confidence = min(0.9, area / 20000.0)
                    
                    detection = VisualDetection(
                        hazard_type=VisualHazard.FIRE_SMOKE,
                        confidence=confidence,
                        bounding_box=(x, y, w, h),
                        description="Potential fire or smoke detected",
                        timestamp=datetime.now(),
                        severity=1.0  # Highest severity
                    )
                    detections.append(detection)
        
        except Exception as e:
            logger.error(f"Error in fire/smoke detection: {e}")
        
        return detections
    
    async def _detect_spills(self, image: np.ndarray) -> List[VisualDetection]:
        """Detect liquid spills on the ground"""
        detections = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect reflective surfaces (spills often reflect light differently)
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (15, 15), 0)
            
            # Find areas with unusual brightness patterns
            diff = cv2.absdiff(gray, blurred)
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            
            # Morphological operations to connect nearby regions
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
            closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 5000:  # Significant spill area
                    # Check if the shape is roughly horizontal (like a spill)
                    rect = cv2.minAreaRect(contour)
                    w, h = rect[1]
                    aspect_ratio = max(w, h) / min(w, h)
                    
                    if aspect_ratio > 2:  # Elongated shape suggests spill
                        x, y, w, h = cv2.boundingRect(contour)
                        confidence = min(0.7, area / 20000.0)
                        
                        detection = VisualDetection(
                            hazard_type=VisualHazard.LIQUID_SPILL,
                            confidence=confidence,
                            bounding_box=(x, y, w, h),
                            description="Potential liquid spill detected",
                            timestamp=datetime.now(),
                            severity=0.7
                        )
                        detections.append(detection)
        
        except Exception as e:
            logger.error(f"Error in spill detection: {e}")
        
        return detections
    
    def _group_lines(self, lines: np.ndarray, distance_threshold: float = 20.0) -> List[List]:
        """Group nearby lines together"""
        if lines is None or len(lines) == 0:
            return []
        
        groups = []
        used = set()
        
        for i, line1 in enumerate(lines):
            if i in used:
                continue
            
            group = [line1]
            used.add(i)
            
            for j, line2 in enumerate(lines):
                if j in used or i == j:
                    continue
                
                # Calculate distance between line endpoints
                x1, y1, x2, y2 = line1[0]
                x3, y3, x4, y4 = line2[0]
                
                # Check if lines are close to each other
                min_dist = min(
                    np.sqrt((x1-x3)**2 + (y1-y3)**2),
                    np.sqrt((x1-x4)**2 + (y1-y4)**2),
                    np.sqrt((x2-x3)**2 + (y2-y3)**2),
                    np.sqrt((x2-x4)**2 + (y2-y4)**2)
                )
                
                if min_dist < distance_threshold:
                    group.append(line2)
                    used.add(j)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def get_current_detections(self) -> List[VisualDetection]:
        """Get current frame detections"""
        return self.current_detections.copy()
    
    def get_detection_summary(self) -> Dict[str, Any]:
        """Get summary of current detections"""
        if not self.current_detections:
            return {'total': 0, 'by_type': {}, 'max_severity': 0.0}
        
        by_type = {}
        for detection in self.current_detections:
            hazard_type = detection.hazard_type.value
            if hazard_type not in by_type:
                by_type[hazard_type] = []
            by_type[hazard_type].append(detection)
        
        max_severity = max(det.severity for det in self.current_detections)
        
        return {
            'total': len(self.current_detections),
            'by_type': {k: len(v) for k, v in by_type.items()},
            'max_severity': max_severity,
            'critical_count': len([d for d in self.current_detections if d.severity >= self.severity_threshold])
        }
    
    def visualize_detections(self, image: np.ndarray) -> np.ndarray:
        """Draw detection results on image"""
        vis_image = image.copy()
        
        for detection in self.current_detections:
            x, y, w, h = detection.bounding_box
            
            # Choose color based on severity
            if detection.severity >= 0.8:
                color = (0, 0, 255)  # Red for high severity
            elif detection.severity >= 0.6:
                color = (0, 165, 255)  # Orange for medium severity
            else:
                color = (0, 255, 255)  # Yellow for low severity
            
            # Draw bounding box
            cv2.rectangle(vis_image, (x, y), (x + w, y + h), color, 2)
            
            # Add label
            label = f"{detection.hazard_type.value}: {detection.confidence:.2f}"
            cv2.putText(vis_image, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return vis_image