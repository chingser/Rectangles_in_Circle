#!/usr/bin/env python3
"""
Rechtecke in Kreis - Kern-Logik (ohne GUI)
Kann unabhängig von Tkinter verwendet werden
"""

import math
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Position:
    """2D Position"""
    x: float
    y: float


@dataclass
class Circle:
    """Kreis mit Radius und Position"""
    radius: float
    position: Position


class Rectangle:
    """Rechteck mit Position, Abmessungen und Rotation"""

    def __init__(self, position: Position, width: float, height: float, rotation: float = 0):
        self.position = position
        self.width = width
        self.height = height
        self.rotation = rotation  # in Grad

    def get_corners(self) -> List[Position]:
        """Gibt die vier Ecken des Rechtecks zurück (mit Rotation)"""
        rad = math.radians(self.rotation)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)

        hw = self.width / 2.0
        hh = self.height / 2.0

        # Ecken relativ zum Zentrum
        local_corners = [
            (-hw, -hh),
            (hw, -hh),
            (hw, hh),
            (-hw, hh)
        ]

        corners = []
        for lx, ly in local_corners:
            # Rotation anwenden
            rx = lx * cos_r - ly * sin_r
            ry = lx * sin_r + ly * cos_r
            corners.append(Position(self.position.x + rx, self.position.y + ry))

        return corners


# ============================================================================
# Kollisionserkennung mit Separating Axis Theorem (SAT)
# ============================================================================

def dot_product(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
    """Berechnet das Skalarprodukt zweier Vektoren"""
    return v1[0] * v2[0] + v1[1] * v2[1]


def normalize_vector(v: Tuple[float, float]) -> Tuple[float, float]:
    """Normalisiert einen Vektor"""
    length = math.sqrt(v[0]**2 + v[1]**2)
    if length == 0:
        return (0, 0)
    return (v[0] / length, v[1] / length)


def get_edge_normal(v1: Tuple[float, float], v2: Tuple[float, float]) -> Tuple[float, float]:
    """Berechnet die Normale (senkrecht) zu einem Edge-Vektor"""
    edge = (v2[0] - v1[0], v2[1] - v1[1])
    # Senkrechte: (-y, x)
    return normalize_vector((-edge[1], edge[0]))


def project_polygon(axis: Tuple[float, float], vertices: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Projiziert alle Vertices auf eine Achse, gibt (min, max) zurück"""
    projections = [dot_product(axis, vertex) for vertex in vertices]
    return (min(projections), max(projections))


def projections_overlap(proj1: Tuple[float, float], proj2: Tuple[float, float], tolerance: float = 0.0) -> bool:
    """Prüft ob zwei 1D-Projektionen überlappen
    
    Args:
        proj1: Erste Projektion (min, max)
        proj2: Zweite Projektion (min, max)
        tolerance: Mindestabstand zwischen Projektionen (mm)
    
    Returns:
        True wenn Überlappung (unter Berücksichtigung der Toleranz)
        
    Note:
        Gap calculation: gap = min(proj1_max, proj2_max) - max(proj1_min, proj2_min)
        - gap > 0: projections overlap
        - gap = 0: projections touch (share one point)
        - gap < 0: projections are separated by |gap|
        
        When tolerance = 0: Allow touching (gap = 0), reject overlap (gap > 0)
        When tolerance > 0: Reject if separation < tolerance (gap > -tolerance)
    """
    # Epsilon for floating-point comparison
    epsilon = 1e-6
    
    # Calculate gap: positive = overlap, zero = touching, negative = separated
    gap = min(proj1[1], proj2[1]) - max(proj1[0], proj2[0])
    
    # Special case: when tolerance is essentially zero, only flag actual overlap
    if tolerance < epsilon:
        # Only return True for actual overlap, not touching
        # gap > epsilon means they actually overlap (not just touching)
        return gap > epsilon
    else:
        # When tolerance > 0, flag if they're closer than tolerance
        # gap > -tolerance means separation is less than required tolerance
        return gap > -tolerance - epsilon



def sat_rectangles_collide(rect1_corners: List[Tuple[float, float]],
                           rect2_corners: List[Tuple[float, float]],
                           tolerance: float = 0.0) -> bool:
    """
    Prüft ob zwei Rechtecke kollidieren mittels Separating Axis Theorem (SAT)

    Args:
        rect1_corners: 4 Eckpunkte des ersten Rechtecks [(x,y), ...]
        rect2_corners: 4 Eckpunkte des zweiten Rechtecks [(x,y), ...]
        tolerance: Mindestabstand zwischen Rechtecken (mm)

    Returns:
        True wenn Kollision/Überlappung (inkl. Toleranz), False wenn getrennt
    """
    # Teste alle Achsen von beiden Rechtecken
    for i in range(4):
        # Achsen von Rechteck 1
        axis1 = get_edge_normal(rect1_corners[i], rect1_corners[(i+1) % 4])
        proj1_r1 = project_polygon(axis1, rect1_corners)
        proj1_r2 = project_polygon(axis1, rect2_corners)

        if not projections_overlap(proj1_r1, proj1_r2, tolerance):
            return False  # Separating Axis gefunden -> keine Kollision

        # Achsen von Rechteck 2
        axis2 = get_edge_normal(rect2_corners[i], rect2_corners[(i+1) % 4])
        proj2_r1 = project_polygon(axis2, rect1_corners)
        proj2_r2 = project_polygon(axis2, rect2_corners)

        if not projections_overlap(proj2_r1, proj2_r2, tolerance):
            return False  # Separating Axis gefunden -> keine Kollision

    return True  # Keine Separating Axis gefunden -> Kollision!


def rectangles_overlap(rect1: Rectangle, rect2: Rectangle, tolerance: float = 0.0) -> bool:
    """
    Prüft ob zwei Rectangle-Objekte überlappen

    Args:
        rect1: Erstes Rechteck
        rect2: Zweites Rechteck
        tolerance: Mindestabstand zwischen Rechtecken (mm)

    Returns:
        True wenn Überlappung (inkl. Toleranz), False sonst
    """
    corners1 = [(c.x, c.y) for c in rect1.get_corners()]
    corners2 = [(c.x, c.y) for c in rect2.get_corners()]
    return sat_rectangles_collide(corners1, corners2, tolerance)


def rectangle_overlaps_any(rect: Rectangle, placed_rectangles: List[Rectangle], tolerance: float = 0.0) -> bool:
    """
    Prüft ob ein Rechteck mit einem der bereits platzierten Rechtecke überlappt

    Args:
        rect: Zu prüfendes Rechteck
        placed_rectangles: Liste bereits platzierter Rechtecke
        tolerance: Mindestabstand zwischen Rechtecken (mm)

    Returns:
        True wenn Überlappung mit mindestens einem Rechteck, False sonst
    """
    for placed_rect in placed_rectangles:
        if rectangles_overlap(rect, placed_rect, tolerance):
            return True
    return False


# ============================================================================


class PackingResult:
    """Ergebnis einer Platzierungsstrategie"""

    def __init__(self):
        self.rectangles: List[Rectangle] = []
        self.circle: Circle = None
        self.count: int = 0
        self.strategy: str = ""
        # Efficiency metrics
        self.efficiency: float = 0.0  # % of circle area used
        self.waste: float = 0.0  # % of circle area wasted
        self.used_area: float = 0.0  # Total area of rectangles
        self.total_area: float = 0.0  # Total circle area


class RectanglePacker:
    """Optimierungsalgorithmus für Rechtecksplatzierung mit Überlappungs-Check"""

    def __init__(self, circle_diameter: float, rect_width: float, rect_height: float, 
                 tolerance: float = 0.0, safe_zone: float = 0.0):
        """
        Args:
            circle_diameter: Durchmesser des Kreises (mm)
            rect_width: Breite der Rechtecke (mm)
            rect_height: Höhe der Rechtecke (mm)
            tolerance: Mindestabstand zwischen Rechtecken (mm)
            safe_zone: Mindestabstand vom Kreisrand (mm)
        """
        self.circle_diameter = circle_diameter
        self.rect_width = rect_width
        self.rect_height = rect_height
        self.radius = circle_diameter / 2.0
        self.tolerance = tolerance
        self.safe_zone = safe_zone
        # Effective radius considering safe zone
        self.effective_radius = self.radius - safe_zone

    def find_optimal_packing(self) -> PackingResult:
        """Findet die optimale Platzierung durch Testen verschiedener Strategien"""
        results = []

        # Strict Grid Strategie - nur orthogonale Orientierungen
        # Angled grids (15°, 30°, etc.) interfere with void-filling algorithm
        # and cause overlaps, so we only test 0° and 90°
        results.append(self._strict_grid_packing(0))
        results.append(self._strict_grid_packing(90))

        # Filter out results with overlaps (final validation)
        valid_results = []
        for result in results:
            if self._validate_no_overlaps(result.rectangles):
                valid_results.append(result)
        
        # Finde die beste Lösung (maximale Anzahl) aus validen Ergebnissen
        if valid_results:
            best = max(valid_results, key=lambda r: r.count)
        else:
            # Fallback: take best even if has overlaps (shouldn't happen with orthogonal only)
            best = max(results, key=lambda r: r.count) if results else PackingResult()
        
        # Calculate efficiency metrics
        self._calculate_efficiency(best)
        
        return best
    
    def _validate_no_overlaps(self, rectangles: List[Rectangle]) -> bool:
        """Validates that no rectangles overlap in the final result
        
        Args:
            rectangles: List of rectangles to validate
            
        Returns:
            True if no overlaps exist, False if any overlap is found
        """
        for i in range(len(rectangles)):
            for j in range(i + 1, len(rectangles)):
                if rectangles_overlap(rectangles[i], rectangles[j], self.tolerance):
                    return False
        return True
    
    def _calculate_efficiency(self, result: PackingResult) -> None:
        """Berechnet die Packing-Effizienz
        
        Args:
            result: PackingResult Objekt (wird in-place modifiziert)
        """
        if result.circle is None:
            return
            
        # Total circle area
        result.total_area = math.pi * (result.circle.radius ** 2)
        
        # Used area (sum of all rectangle areas)
        result.used_area = sum(self.rect_width * self.rect_height for _ in result.rectangles)
        
        # Efficiency percentage
        if result.total_area > 0:
            result.efficiency = (result.used_area / result.total_area) * 100.0
            result.waste = 100.0 - result.efficiency
        else:
            result.efficiency = 0.0
            result.waste = 100.0

    def _strict_grid_packing(self, rotation: float) -> PackingResult:
        """
        Strikte Grid-Platzierung.
        Platziert Rechtecke in einem festen Raster.
        Testet verschiedene Offsets, um die optimale Ausrichtung zu finden.
        Versucht zusätzlich, Lücken am Rand mit gedrehten Rechtecken zu füllen.
        
        Args:
            rotation: Rotation der Rechtecke (0 oder 90 Grad)
            
        Returns:
            PackingResult
        """
        result = PackingResult()
        result.circle = Circle(self.radius, Position(0, 0))
        result.strategy = f"Strict Grid (Rot: {rotation}° + Fill)"
        
        # Rechteck-Dimensionen basierend auf Rotation
        if rotation == 90:
            w, h = self.rect_height, self.rect_width
            alt_rotation = 0
        else:
            w, h = self.rect_width, self.rect_height
            alt_rotation = 90
            
        # Dimensionen für gedrehte Rechtecke
        ortho_w, ortho_h = h, w
        
        # Grid spacing includes tolerance
        grid_step_x = w + self.tolerance
        grid_step_y = h + self.tolerance
        ortho_step_x = ortho_w + self.tolerance
        ortho_step_y = ortho_h + self.tolerance
            
        best_rects = []
        max_count = 0
        
        # Teste Offsets von 0 bis grid_step in kleinen Schritten
        steps_x = 10
        steps_y = 10
        
        for i in range(steps_x):
            for j in range(steps_y):
                offset_x = (grid_step_x / steps_x) * i
                offset_y = (grid_step_y / steps_y) * j
                
                current_rects = []
                
                # Grid generieren
                start_x = -self.radius - w
                start_y = -self.radius - h
                
                cols = int((self.circle_diameter + 2*w) / grid_step_x) + 2
                rows = int((self.circle_diameter + 2*h) / grid_step_y) + 2
                
                # Bounds tracking
                min_x = float('inf')
                max_x = float('-inf')
                min_y = float('inf')
                max_y = float('-inf')
                
                for r in range(rows):
                    for c in range(cols):
                        x = start_x + c * grid_step_x + offset_x
                        y = start_y + r * grid_step_y + offset_y
                        
                        center_x = x + w/2
                        center_y = y + h/2
                        
                        pos = Position(center_x, center_y)
                        rect = Rectangle(pos, self.rect_width, self.rect_height, rotation)
                        
                        if self._rectangle_fits_in_circle(rect):
                            current_rects.append(rect)
                            # Update bounds (using edges)
                            min_x = min(min_x, center_x - w/2)
                            max_x = max(max_x, center_x + w/2)
                            min_y = min(min_y, center_y - h/2)
                            max_y = max(max_y, center_y + h/2)
                
                # Lücken füllen mit gedrehten Rechtecken (Scanning Strategy)
                if current_rects:
                    filled_rects = list(current_rects)
                    
                    # 1. Fill Right
                    # Start at max_x of grid
                    curr_x = max_x + self.tolerance + ortho_w/2
                    while curr_x - ortho_w/2 < self.radius:
                        # Scan Y
                        # Align with min_y of grid to keep structure
                        start_scan_y = min_y + ortho_h/2
                        # We scan a bit below and above to catch all space
                        # Range: -radius to radius
                        
                        # Calculate start index to align with grid
                        # y = start_scan_y + k * ortho_step_y
                        # We want y approx -radius
                        k_start = int((-self.radius - start_scan_y) / ortho_step_y) - 1
                        k_end = int((self.radius - start_scan_y) / ortho_step_y) + 2
                        
                        for k in range(k_start, k_end):
                            curr_y = start_scan_y + k * ortho_step_y
                            
                            new_rect = Rectangle(Position(curr_x, curr_y), self.rect_width, self.rect_height, alt_rotation)
                            
                            if self._rectangle_fits_in_circle(new_rect):
                                if not rectangle_overlaps_any(new_rect, filled_rects, self.tolerance):
                                    filled_rects.append(new_rect)
                        
                        curr_x += ortho_step_x

                    # 2. Fill Left
                    curr_x = min_x - self.tolerance - ortho_w/2
                    while curr_x + ortho_w/2 > -self.radius:
                        # Scan Y (same logic)
                        start_scan_y = min_y + ortho_h/2
                        k_start = int((-self.radius - start_scan_y) / ortho_step_y) - 1
                        k_end = int((self.radius - start_scan_y) / ortho_step_y) + 2
                        
                        for k in range(k_start, k_end):
                            curr_y = start_scan_y + k * ortho_step_y
                            new_rect = Rectangle(Position(curr_x, curr_y), self.rect_width, self.rect_height, alt_rotation)
                            
                            if self._rectangle_fits_in_circle(new_rect):
                                if not rectangle_overlaps_any(new_rect, filled_rects, self.tolerance):
                                    filled_rects.append(new_rect)
                        
                        curr_x -= ortho_step_x
                        
                    # 3. Fill Top (Optional, usually covered by main grid if aspect ratio allows, but good for completeness)
                    # Only if ortho_h is small enough to fit? 
                    # For 50x10 main (flat), ortho is 10x50 (tall). 
                    # Top gap is wide and short. 10x50 won't fit well.
                    # But if main is 10x50 (tall), ortho is 50x10 (flat).
                    # Then Top gap is good for 50x10.
                    
                    curr_y = max_y + self.tolerance + ortho_h/2
                    while curr_y - ortho_h/2 < self.radius:
                         # Scan X
                        start_scan_x = min_x + ortho_w/2
                        k_start = int((-self.radius - start_scan_x) / ortho_step_x) - 1
                        k_end = int((self.radius - start_scan_x) / ortho_step_x) + 2
                        
                        for k in range(k_start, k_end):
                            curr_x = start_scan_x + k * ortho_step_x
                            new_rect = Rectangle(Position(curr_x, curr_y), self.rect_width, self.rect_height, alt_rotation)
                            
                            if self._rectangle_fits_in_circle(new_rect):
                                if not rectangle_overlaps_any(new_rect, filled_rects, self.tolerance):
                                    filled_rects.append(new_rect)
                        curr_y += ortho_step_y

                    # 4. Fill Bottom
                    curr_y = min_y - self.tolerance - ortho_h/2
                    while curr_y + ortho_h/2 > -self.radius:
                         # Scan X
                        start_scan_x = min_x + ortho_w/2
                        k_start = int((-self.radius - start_scan_x) / ortho_step_x) - 1
                        k_end = int((self.radius - start_scan_x) / ortho_step_x) + 2
                        
                        for k in range(k_start, k_end):
                            curr_x = start_scan_x + k * ortho_step_x
                            new_rect = Rectangle(Position(curr_x, curr_y), self.rect_width, self.rect_height, alt_rotation)
                            
                            if self._rectangle_fits_in_circle(new_rect):
                                if not rectangle_overlaps_any(new_rect, filled_rects, self.tolerance):
                                    filled_rects.append(new_rect)
                        curr_y -= ortho_step_y

                    if len(filled_rects) > max_count:
                        max_count = len(filled_rects)
                        best_rects = filled_rects
                        
                    # 5. Center Fill Top/Bottom (Parallel)
                    # Try to place rectangles centered horizontally at the top and bottom
                    # This helps when the grid columns don't fit, but a centered rect does.
                    
                    # Top Center
                    curr_y = max_y + self.tolerance + h/2
                    while curr_y + h/2 <= self.radius:
                        # Center X relative to the grid bounds? Or absolute center?
                        # Absolute center (0) is usually best for symmetry in a circle.
                        # But we should align with the grid's center line if possible.
                        # The grid is shifted by offset_x.
                        # Grid center line is approx offset_x?
                        # Let's try absolute center first, as it maximizes space in circle.
                        # But it might not align with grid lines.
                        # User wants "centered above the middle grid line".
                        # If grid has even columns, middle line is at offset_x + k*w.
                        # Let's try to align with the center of the bounding box of the grid.
                        grid_center_x = (min_x + max_x) / 2
                        
                        new_rect = Rectangle(Position(grid_center_x, curr_y), self.rect_width, self.rect_height, rotation)
                        
                        if self._rectangle_fits_in_circle(new_rect):
                            if not rectangle_overlaps_any(new_rect, filled_rects, self.tolerance):
                                filled_rects.append(new_rect)
                                # Update max_y so we can stack more if possible?
                                # But we are outside the loop.
                                # Let's just do one or two layers.
                                curr_y += grid_step_y
                            else:
                                break
                        else:
                            break
                            
                    # Bottom Center
                    curr_y = min_y - self.tolerance - h/2
                    while curr_y - h/2 >= -self.radius:
                        grid_center_x = (min_x + max_x) / 2
                        new_rect = Rectangle(Position(grid_center_x, curr_y), self.rect_width, self.rect_height, rotation)
                        
                        if self._rectangle_fits_in_circle(new_rect):
                            if not rectangle_overlaps_any(new_rect, filled_rects, self.tolerance):
                                filled_rects.append(new_rect)
                                curr_y -= grid_step_y
                            else:
                                break
                        else:
                            break
                            
                    if len(filled_rects) > max_count:
                        max_count = len(filled_rects)
                        best_rects = filled_rects
                else:
                    # Fallback if no rects fit in main grid (e.g. huge rect, small circle)
                    # Try to place at least one?
                    pass
        
        # Apply systematic gap filling to best result
        if best_rects:
            best_rects = self._systematic_gap_fill(best_rects)
            max_count = len(best_rects)
                    
        result.rectangles = best_rects
        result.count = max_count
        return result



    def _rectangle_fits_in_circle(self, rect: Rectangle) -> bool:
        """
        Prüft ob alle Ecken des Rechtecks im Kreis liegen (unter Berücksichtigung der Safe Zone)

        Args:
            rect: Zu prüfendes Rechteck

        Returns:
            True wenn alle Ecken im effektiven Kreis (mit Safe Zone), False sonst
        """
        corners = rect.get_corners()

        for corner in corners:
            distance = math.sqrt(corner.x ** 2 + corner.y ** 2)
            # Check against effective radius (radius - safe_zone)
            if distance > self.effective_radius:
                return False

        return True

    def _get_bounding_box(self, corners: List[Position]) -> Tuple[float, float, float, float]:
        """
        Berechnet die Bounding Box von Eckpunkten
        
        Args:
            corners: Liste von Eckpunkten
            
        Returns:
            Tuple (min_x, min_y, max_x, max_y)
        """
        xs = [c.x for c in corners]
        ys = [c.y for c in corners]
        return (min(xs), min(ys), max(xs), max(ys))

    def _generate_edge_positions(self, rect: Rectangle, new_rotation: float) -> List[Position]:
        """
        Generiert Kandidatenpositionen neben den Kanten eines Rechtecks
        
        Args:
            rect: Existierendes Rechteck
            new_rotation: Rotation des neuen Rechtecks (0 oder 90)
            
        Returns:
            Liste von Positionen wo ein neues Rechteck platziert werden könnte
        """
        positions = []
        
        # Dimensionen basierend auf Rotation
        if new_rotation == 90:
            new_w, new_h = self.rect_height, self.rect_width
        else:
            new_w, new_h = self.rect_width, self.rect_height
        
        # Nur für achsenausgerichtete Rechtecke
        if rect.rotation in [0, 90]:
            corners = rect.get_corners()
            bbox = self._get_bounding_box(corners)
            
            # Rechte Kante
            positions.append(Position(
                bbox[2] + self.tolerance + new_w/2,
                rect.position.y
            ))
            
            # Linke Kante
            positions.append(Position(
                bbox[0] - self.tolerance - new_w/2,
                rect.position.y
            ))
            
            # Obere Kante
            positions.append(Position(
                rect.position.x,
                bbox[3] + self.tolerance + new_h/2
            ))
            
            # Untere Kante
            positions.append(Position(
                rect.position.x,
                bbox[1] - self.tolerance - new_h/2
            ))
        
        return positions

    def _touches_existing(self, rect: Rectangle, placed_rectangles: List[Rectangle]) -> bool:
        """
        Prüft ob ein Rechteck mindestens ein existierendes Rechteck berührt
        
        Args:
            rect: Zu prüfendes Rechteck
            placed_rectangles: Liste bereits platzierter Rechtecke
            
        Returns:
            True wenn das Rechteck mindestens ein anderes berührt (oder wenn tolerance > 0)
        """
        # Wenn Toleranz > 0, nicht erforderlich dass sie sich berühren
        if self.tolerance > 1e-6:
            return True
        
        # Prüfe ob eine Kante sehr nahe (berührend) an einem anderen Rechteck ist
        epsilon = 1e-3
        
        for placed in placed_rectangles:
            # Für achsenausgerichtete Rechtecke, prüfe Bounding Box Distanz
            if rect.rotation in [0, 90] and placed.rotation in [0, 90]:
                rect_bbox = self._get_bounding_box(rect.get_corners())
                placed_bbox = self._get_bounding_box(placed.get_corners())
                
                # Prüfe ob sie eine Kante teilen (Abstand ≈ 0)
                # Horizontal touching
                if abs(rect_bbox[0] - placed_bbox[2]) < epsilon or abs(rect_bbox[2] - placed_bbox[0]) < epsilon:
                    # Check vertical overlap
                    if not (rect_bbox[3] < placed_bbox[1] - epsilon or rect_bbox[1] > placed_bbox[3] + epsilon):
                        return True
                
                # Vertical touching
                if abs(rect_bbox[1] - placed_bbox[3]) < epsilon or abs(rect_bbox[3] - placed_bbox[1]) < epsilon:
                    # Check horizontal overlap
                    if not (rect_bbox[2] < placed_bbox[0] - epsilon or rect_bbox[0] > placed_bbox[2] + epsilon):
                        return True
        
        return False

    def _systematic_gap_fill(self, placed_rectangles: List[Rectangle]) -> List[Rectangle]:
        """
        Systematically scans the entire circle to fill empty spaces
        
        Args:
            placed_rectangles: Already placed rectangles
            
        Returns:
            Extended list with additional rectangles
        """
        filled_rects = list(placed_rectangles)
        
        # Use fine-grained scanning - smaller step means more thorough but slower
        scan_step = min(self.rect_width, self.rect_height) / 2.0
        
        # Scan the entire circular area
        y = -self.radius
        while y <= self.radius:
            x = -self.radius
            while x <= self.radius:
                # Try both orientations at each position
                for rotation in [0, 90]:
                    rect = Rectangle(Position(x, y), self.rect_width, self.rect_height, rotation)
                    
                    if (self._rectangle_fits_in_circle(rect) and 
                        not rectangle_overlaps_any(rect, filled_rects, self.tolerance)):
                        filled_rects.append(rect)
                        break  # Found a placement, move to next position
                
                x += scan_step
            y += scan_step
        
        return filled_rects


