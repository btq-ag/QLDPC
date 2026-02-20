"""
Isometric 3D renderer for quantum circuit visualization.

This module handles the 2.5D isometric projection of 3D components
onto a 2D tkinter canvas.
Author: Jeffrey Morais"""

import math
import tkinter as tk
from typing import List, Tuple

from ..config import DEFAULT_CONFIG


class IsometricRenderer:
    """
    Handles 2.5D isometric rendering of 3D components on a tkinter canvas.
    
    This class provides methods to convert 3D coordinates to 2D isometric
    projections and render quantum circuit components as 3D blocks.
    """
    
    def __init__(self, canvas: tk.Canvas, scale: float = None, config=None):
        """
        Initialize the isometric renderer.
        
        Args:
            canvas: tkinter Canvas widget for rendering
            scale: Scaling factor for isometric projection
            config: Configuration object
        """
        self.canvas = canvas
        self.config = config or DEFAULT_CONFIG
        self.scale = scale or self.config.grid.default_scale
        self.offset_x = self.config.grid.default_offset_x
        self.offset_y = self.config.grid.default_offset_y
        
        # Isometric projection angles (30 degrees)
        self.cos_30 = math.cos(math.radians(30))
        self.sin_30 = math.sin(math.radians(30))
    
    def project_3d_to_2d(self, x: float, y: float, z: float) -> Tuple[float, float]:
        """
        Convert 3D coordinates to 2D isometric projection.
        
        Args:
            x, y, z: 3D coordinates
            
        Returns:
            Tuple of 2D screen coordinates
        """
        iso_x = (x - y) * self.cos_30 * self.scale + self.offset_x
        iso_y = (x + y) * self.sin_30 * self.scale - z * self.scale + self.offset_y
        return iso_x, iso_y
    
    def screen_to_grid(self, screen_x: float, screen_y: float) -> Tuple[int, int]:
        """
        Convert screen coordinates to grid coordinates.
        
        This is an approximate inverse of the isometric projection.
        
        Args:
            screen_x, screen_y: Screen coordinates
            
        Returns:
            Tuple of (grid_x, grid_y) integer coordinates
        """
        relative_x = screen_x - self.offset_x
        relative_y = screen_y - self.offset_y
        
        # Approximate inverse projection
        grid_x = round((relative_x / self.scale / self.cos_30 + 
                       relative_y / self.scale / self.sin_30) / 2)
        grid_y = round((relative_y / self.scale / self.sin_30 - 
                       relative_x / self.scale / self.cos_30) / 2)
        
        return grid_x, grid_y
    
    def draw_cube(self, x: float, y: float, z: float, 
                  width: float, height: float, depth: float,
                  color: Tuple[float, float, float], 
                  outline: str = "#333333") -> List[int]:
        """
        Draw a 3D cube using isometric projection.
        
        In this isometric projection:
        - +x axis goes to the lower-right
        - +y axis goes to the lower-left  
        - +z axis goes straight up
        
        Args:
            x, y, z: Bottom-left-front corner position
            width, height, depth: Cube dimensions (width=x, height=z, depth=y)
            color: RGB color tuple (0-1 range)
            outline: Outline color hex string
            
        Returns:
            List of canvas item IDs for the rendered cube
        """
        # Define cube vertices
        vertices = [
            (x, y, z),                          # 0: bottom-front-left
            (x + width, y, z),                  # 1: bottom-front-right
            (x + width, y + depth, z),          # 2: bottom-back-right
            (x, y + depth, z),                  # 3: bottom-back-left
            (x, y, z + height),                 # 4: top-front-left
            (x + width, y, z + height),         # 5: top-front-right
            (x + width, y + depth, z + height), # 6: top-back-right
            (x, y + depth, z + height)          # 7: top-back-left
        ]
        
        # Project vertices to 2D
        projected = [self.project_3d_to_2d(*v) for v in vertices]
        
        items = []
        
        # Draw all 6 faces from back to front (Painter's Algorithm)
        
        # Bottom face (darkest)
        bottom_color = self._brighten_color(color, 0.5)
        bottom_hex = self._rgb_to_hex(bottom_color)
        items.append(self.canvas.create_polygon(
            projected[0][0], projected[0][1],
            projected[1][0], projected[1][1],
            projected[2][0], projected[2][1],
            projected[3][0], projected[3][1],
            fill=bottom_hex, outline=outline, width=1
        ))
        
        # Back-right face
        back_right_color = self._brighten_color(color, 0.6)
        back_right_hex = self._rgb_to_hex(back_right_color)
        items.append(self.canvas.create_polygon(
            projected[2][0], projected[2][1],
            projected[3][0], projected[3][1],
            projected[7][0], projected[7][1],
            projected[6][0], projected[6][1],
            fill=back_right_hex, outline=outline, width=1
        ))
        
        # Back-left face
        back_left_color = self._brighten_color(color, 0.55)
        back_left_hex = self._rgb_to_hex(back_left_color)
        items.append(self.canvas.create_polygon(
            projected[1][0], projected[1][1],
            projected[2][0], projected[2][1],
            projected[6][0], projected[6][1],
            projected[5][0], projected[5][1],
            fill=back_left_hex, outline=outline, width=1
        ))
        
        # Left face (front-left)
        left_color = self._brighten_color(color, 0.7)
        left_hex = self._rgb_to_hex(left_color)
        items.append(self.canvas.create_polygon(
            projected[0][0], projected[0][1],
            projected[3][0], projected[3][1],
            projected[7][0], projected[7][1],
            projected[4][0], projected[4][1],
            fill=left_hex, outline=outline, width=1
        ))
        
        # Right face (front-right)
        right_color = self._brighten_color(color, 0.85)
        right_hex = self._rgb_to_hex(right_color)
        items.append(self.canvas.create_polygon(
            projected[0][0], projected[0][1],
            projected[1][0], projected[1][1],
            projected[5][0], projected[5][1],
            projected[4][0], projected[4][1],
            fill=right_hex, outline=outline, width=1
        ))
        
        # Top face (lightest)
        top_color = self._brighten_color(color, 1.1)
        top_hex = self._rgb_to_hex(top_color)
        items.append(self.canvas.create_polygon(
            projected[4][0], projected[4][1],
            projected[5][0], projected[5][1],
            projected[6][0], projected[6][1],
            projected[7][0], projected[7][1],
            fill=top_hex, outline=outline, width=1
        ))
        
        return items
    
    def draw_grid(self, grid_range: int = None, grid_z: float = -0.05) -> None:
        """
        Draw the isometric grid for circuit mode.
        
        Args:
            grid_range: Range of grid coordinates (default from config)
            grid_z: Z-position of grid (slightly below 0 so cubes sit on top)
        """
        if grid_range is None:
            grid_range = self.config.grid.max_coord
        
        grid_color = self.config.colors.grid_line
        boundary_color = self.config.colors.grid_boundary
        
        for i in range(-grid_range, grid_range + 1):
            for j in range(-grid_range, grid_range + 1):
                x1, y1 = self.project_3d_to_2d(i, j, grid_z)
                x2, y2 = self.project_3d_to_2d(i + 1, j, grid_z)
                x3, y3 = self.project_3d_to_2d(i, j + 1, grid_z)
                
                # Use boundary color for edge lines
                is_boundary = (i == -grid_range or i == grid_range or 
                              j == -grid_range or j == grid_range)
                color = boundary_color if is_boundary else grid_color
                
                if i < grid_range:
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, tags="grid")
                if j < grid_range:
                    self.canvas.create_line(x1, y1, x3, y3, fill=color, tags="grid")
    
    def draw_mini_cube(self, canvas: tk.Canvas, cx: float, cy: float, 
                       color: Tuple[float, float, float], depth: float = 1.0) -> None:
        """
        Draw a small isometric cube on a canvas (for legend).
        
        Args:
            canvas: Canvas to draw on
            cx, cy: Center position
            color: RGB color tuple
            depth: Depth multiplier (2.0 for two-qubit gates)
        """
        size = 12
        size_depth = size * depth
        
        def project(x, y, z):
            iso_x = (x - y) * self.cos_30 + cx
            iso_y = (x + y) * self.sin_30 - z + cy
            return iso_x, iso_y
        
        # 8 vertices
        v = [
            project(0, 0, 0),
            project(size, 0, 0),
            project(size, size_depth, 0),
            project(0, size_depth, 0),
            project(0, 0, size),
            project(size, 0, size),
            project(size, size_depth, size),
            project(0, size_depth, size),
        ]
        
        outline = '#444'
        
        # Draw faces
        canvas.create_polygon(v[0][0], v[0][1], v[1][0], v[1][1],
                             v[2][0], v[2][1], v[3][0], v[3][1],
                             fill=self._rgb_to_hex(self._brighten_color(color, 0.5)), outline=outline)
        
        canvas.create_polygon(v[2][0], v[2][1], v[3][0], v[3][1],
                             v[7][0], v[7][1], v[6][0], v[6][1],
                             fill=self._rgb_to_hex(self._brighten_color(color, 0.6)), outline=outline)
        
        canvas.create_polygon(v[1][0], v[1][1], v[2][0], v[2][1],
                             v[6][0], v[6][1], v[5][0], v[5][1],
                             fill=self._rgb_to_hex(self._brighten_color(color, 0.55)), outline=outline)
        
        canvas.create_polygon(v[0][0], v[0][1], v[3][0], v[3][1], 
                             v[7][0], v[7][1], v[4][0], v[4][1],
                             fill=self._rgb_to_hex(self._brighten_color(color, 0.7)), outline=outline)
        
        canvas.create_polygon(v[0][0], v[0][1], v[1][0], v[1][1],
                             v[5][0], v[5][1], v[4][0], v[4][1],
                             fill=self._rgb_to_hex(self._brighten_color(color, 0.85)), outline=outline)
        
        canvas.create_polygon(v[4][0], v[4][1], v[5][0], v[5][1],
                             v[6][0], v[6][1], v[7][0], v[7][1],
                             fill=self._rgb_to_hex(self._brighten_color(color, 1.1)), outline=outline)
    
    @staticmethod
    def _rgb_to_hex(color: Tuple[float, float, float]) -> str:
        """Convert RGB tuple (0-1 range) to hex color string."""
        r, g, b = [int(c * 255) for c in color]
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def _brighten_color(color: Tuple[float, float, float], factor: float) -> Tuple[float, float, float]:
        """Brighten or darken a color by a given factor."""
        return tuple(min(1.0, c * factor) for c in color)
