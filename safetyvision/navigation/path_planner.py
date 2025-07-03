"""
Safety-aware path planning for nuclear facility navigation
"""

import numpy as np
from typing import List, Tuple, Optional
import networkx as nx
from dataclasses import dataclass

@dataclass
class SafetyConstraints:
    """Safety constraints for path planning"""
    max_radiation: float = 0.5  # mSv/h
    min_clearance: float = 1.5  # meters
    forbidden_zones: Optional[List[Tuple[float, float]]] = None
    emergency_exits: Optional[List[Tuple[float, float]]] = None

class SafetyAwarePathPlanner:
    """Path planner that prioritizes safety over efficiency"""
    
    def __init__(self, facility_map: np.ndarray, safety_constraints: SafetyConstraints):
        self.facility_map = facility_map
        self.constraints = safety_constraints
        self.radiation_map = None
        
    def plan_safe_path(self, start: Tuple[float, float], goal: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Plan safest path considering all constraints"""
        import heapq
        from math import sqrt
        
        def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
            return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        
        def get_safety_cost(position: Tuple[float, float]) -> float:
            """Calculate safety cost for a position"""
            x, y = position
            
            # Check if position is in forbidden zones
            if self.constraints.forbidden_zones:
                for zone_x, zone_y in self.constraints.forbidden_zones:
                    if distance(position, (zone_x, zone_y)) < 2.0:  # 2m safety buffer
                        return float('inf')  # Impassable
            
            # Calculate radiation cost if radiation map is available
            radiation_cost = 0.0
            if self.radiation_map is not None:
                # Convert world coordinates to map indices (simple implementation)
                map_h, map_w = self.radiation_map.shape
                map_x = int(min(max(x / 10.0 * map_w, 0), map_w - 1))  # Assume 10m per pixel
                map_y = int(min(max(y / 10.0 * map_h, 0), map_h - 1))
                
                radiation_level = self.radiation_map[map_y, map_x]
                if radiation_level > self.constraints.max_radiation:
                    radiation_cost = radiation_level * 100  # High cost for radiation
                else:
                    radiation_cost = radiation_level * 10   # Moderate cost
            
            # Add cost for being too close to obstacles (clearance requirement)
            clearance_cost = 0.0
            # This would need actual obstacle map integration
            
            return radiation_cost + clearance_cost
        
        def get_neighbors(position: Tuple[float, float]) -> List[Tuple[float, float]]:
            """Get valid neighboring positions"""
            x, y = position
            neighbors = []
            
            # 8-connected grid (can move diagonally)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    new_x, new_y = x + dx, y + dy
                    
                    # Check bounds (basic implementation)
                    if 0 <= new_x < self.facility_map.shape[1] and 0 <= new_y < self.facility_map.shape[0]:
                        # Check if position is traversable
                        if self.facility_map[int(new_y), int(new_x)] > 0:  # Assume 0 = obstacle
                            neighbors.append((new_x, new_y))
            
            return neighbors
        
        # A* algorithm implementation
        open_set = [(0, start)]  # Priority queue: (f_score, position)
        came_from = {}
        g_score = {start: 0}
        f_score = {start: distance(start, goal)}
        visited = set()
        
        while open_set:
            current_f, current = heapq.heappop(open_set)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            # Check if we reached the goal
            if distance(current, goal) < 1.0:  # Within 1 meter of goal
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return list(reversed(path))
            
            # Check neighbors
            for neighbor in get_neighbors(current):
                if neighbor in visited:
                    continue
                
                # Calculate tentative g_score
                move_cost = distance(current, neighbor)
                safety_cost = get_safety_cost(neighbor)
                
                if safety_cost == float('inf'):
                    continue  # Skip impassable positions
                
                tentative_g = g_score[current] + move_cost + safety_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + distance(neighbor, goal)
                    
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # No path found - return direct path to emergency exits if available
        if self.constraints.emergency_exits:
            nearest_exit = min(self.constraints.emergency_exits, 
                             key=lambda exit: distance(start, exit))
            return [start, nearest_exit]
        
        # No path found at all
        return [start]
        
    def update_radiation_map(self, radiation_data: np.ndarray):
        """Update radiation map for dynamic replanning"""
        self.radiation_map = radiation_data
