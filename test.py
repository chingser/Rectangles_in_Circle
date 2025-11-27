#!/usr/bin/env python3
"""
Enhanced test script with detailed overlap diagnostics
"""

import sys
import os
from packing_logic import RectanglePacker, rectangles_overlap
import ezdxf

def test_packing_algorithm():
    """Test the packing algorithm with user's parameters"""
    print("=" * 80)
    print("TEST 1: PACKING ALGORITHM")
    print("=" * 80)
    
    # User's parameters
    circle_diameter = 100.0
    rect_width = 15.0
    rect_height = 10.0
    tolerance = 0.0
    safe_zone = 0.0
    
    print(f"\nParameters:")
    print(f"  Circle Diameter: {circle_diameter} mm")
    print(f"  Rectangle: {rect_width} × {rect_height} mm")
    print(f"  Tolerance: {tolerance} mm")
    print(f"  Safe Zone: {safe_zone} mm")
    
    # Run packing
    packer = RectanglePacker(circle_diameter, rect_width, rect_height, tolerance, safe_zone)
    result = packer.find_optimal_packing()
    
    print(f"\nResults:")
    print(f"  Total Rectangles: {result.count}")
    print(f"  Strategy: {result.strategy}")
    print(f"  Efficiency: {result.efficiency:.2f}%")
    print(f"  Waste: {result.waste:.2f}%")
    
    return result

def test_rotation_angles(result):
    """Test that all rectangles have only 0° or 90° rotation"""
    print("\n" + "=" * 80)
    print("TEST 2: ROTATION ANGLES")
    print("=" * 80)
    
    rotation_counts = {}
    invalid_rotations = []
    
    for idx, rect in enumerate(result.rectangles):
        rotation = rect.rotation
        
        # Count rotations
        if rotation not in rotation_counts:
            rotation_counts[rotation] = 0
        rotation_counts[rotation] += 1
        
        # Check for invalid rotations (not 0° or 90°)
        if rotation not in [0, 90]:
            invalid_rotations.append((idx, rotation))
    
    print(f"\nRotation Distribution:")
    for angle, count in sorted(rotation_counts.items()):
        print(f"  {angle}°: {count} rectangles")
    
    if invalid_rotations:
        print(f"\n❌ FAILED: Found {len(invalid_rotations)} rectangles with invalid rotations:")
        for idx, angle in invalid_rotations[:10]:  # Show first 10
            print(f"  Rectangle #{idx}: {angle}°")
        if len(invalid_rotations) > 10:
            print(f"  ... and {len(invalid_rotations) - 10} more")
        return False
    else:
        print(f"\n✅ PASSED: All rectangles have valid rotations (0° or 90°)")
        return True

def analyze_overlap_details(rect_i, rect_j, idx_i, idx_j):
    """Analyze why two rectangles overlap"""
    corners_i = rect_i.get_corners()
    corners_j = rect_j.get_corners()
    
    # Calculate bounding boxes
    xs_i = [c.x for c in corners_i]
    ys_i = [c.y for c in corners_i]
    xs_j = [c.x for c in corners_j]
    ys_j = [c.y for c in corners_j]
    
    bbox_i = (min(xs_i), min(ys_i), max(xs_i), max(ys_i))
    bbox_j = (min(xs_j), min(ys_j), max(xs_j), max(ys_j))
    
    # Calculate gaps
    gap_x = min(bbox_i[2], bbox_j[2]) - max(bbox_i[0], bbox_j[0])
    gap_y = min(bbox_i[3], bbox_j[3]) - max(bbox_i[1], bbox_j[1])
    
    return {
        'gap_x': gap_x,
        'gap_y': gap_y,
        'bbox_i': bbox_i,
        'bbox_j': bbox_j,
        'distance': ((rect_i.position.x - rect_j.position.x)**2 + 
                    (rect_i.position.y - rect_j.position.y)**2)**0.5
    }

def test_overlaps(result, tolerance):
    """Test that no rectangles overlap"""
    print("\n" + "=" * 80)
    print("TEST 3: OVERLAP DETECTION")
    print("=" * 80)
    
    overlaps = []
    total_checks = 0
    
    print(f"\nChecking {result.count} rectangles for overlaps...")
    print(f"Total pairwise checks: {result.count * (result.count - 1) // 2}")
    
    for i in range(len(result.rectangles)):
        for j in range(i + 1, len(result.rectangles)):
            total_checks += 1
            if rectangles_overlap(result.rectangles[i], result.rectangles[j], tolerance):
                details = analyze_overlap_details(result.rectangles[i], result.rectangles[j], i, j)
                overlaps.append((i, j, details))
    
    print(f"\nCompleted {total_checks} pairwise checks")
    
    if overlaps:
        print(f"\n❌ FAILED: Found {len(overlaps)} overlapping rectangle pairs:")
        
        # Show detailed analysis for first 5 overlaps
        for idx, (i, j, details) in enumerate(overlaps[:5]):
            rect_i = result.rectangles[i]
            rect_j = result.rectangles[j]
            print(f"\n  Overlap #{idx+1}: Rectangle #{i} ↔ #{j}")
            print(f"    Position #{i}: ({rect_i.position.x:.3f}, {rect_i.position.y:.3f}), rot: {rect_i.rotation}°")
            print(f"    Position #{j}: ({rect_j.position.x:.3f}, {rect_j.position.y:.3f}), rot: {rect_j.rotation}°")
            print(f"    Distance between centers: {details['distance']:.3f} mm")
            print(f"    Gap X: {details['gap_x']:.6f} mm")
            print(f"    Gap Y: {details['gap_y']:.6f} mm")
            print(f"    BBox #{i}: ({details['bbox_i'][0]:.3f}, {details['bbox_i'][1]:.3f}) to ({details['bbox_i'][2]:.3f}, {details['bbox_i'][3]:.3f})")
            print(f"    BBox #{j}: ({details['bbox_j'][0]:.3f}, {details['bbox_j'][1]:.3f}) to ({details['bbox_j'][2]:.3f}, {details['bbox_j'][3]:.3f})")
        
        if len(overlaps) > 5:
            print(f"\n  ... and {len(overlaps) - 5} more overlaps")
        
        return False
    else:
        print(f"\n✅ PASSED: No overlaps detected")
        return True

def test_circle_bounds(result, circle_diameter, safe_zone):
    """Test that all rectangles are within circle bounds"""
    print("\n" + "=" * 80)
    print("TEST 4: CIRCLE BOUNDS")
    print("=" * 80)
    
    radius = circle_diameter / 2.0
    effective_radius = radius - safe_zone
    out_of_bounds = []
    
    print(f"\nCircle radius: {radius:.2f} mm")
    print(f"Effective radius (with safe zone): {effective_radius:.2f} mm")
    
    for idx, rect in enumerate(result.rectangles):
        corners = rect.get_corners()
        for corner_idx, corner in enumerate(corners):
            distance = (corner.x ** 2 + corner.y ** 2) ** 0.5
            if distance > effective_radius + 0.001:  # Small epsilon for float precision
                out_of_bounds.append((idx, corner_idx, distance))
    
    if out_of_bounds:
        print(f"\n❌ FAILED: Found {len(out_of_bounds)} corners outside circle bounds:")
        for idx, corner_idx, distance in out_of_bounds[:10]:
            print(f"  Rectangle #{idx}, corner {corner_idx}: distance={distance:.2f} mm (exceeds {effective_radius:.2f} mm)")
        if len(out_of_bounds) > 10:
            print(f"  ... and {len(out_of_bounds) - 10} more")
        return False
    else:
        print(f"\n✅ PASSED: All rectangle corners are within circle bounds")
        return True

def test_dxf_export(result, circle_diameter, safe_zone):
    """Test DXF export functionality"""
    print("\n" + "=" * 80)
    print("TEST 5: DXF EXPORT")
    print("=" * 80)
    
    test_filename = "test_output.dxf"
    
    try:
        # Create DXF document
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Add circle
        msp.add_circle(
            center=(0, 0),
            radius=result.circle.radius,
            dxfattribs={'layer': 'CIRCLE'}
        )
        
        # Add safe zone if present
        if safe_zone > 0:
            msp.add_circle(
                center=(0, 0),
                radius=result.circle.radius - safe_zone,
                dxfattribs={'layer': 'SAFE_ZONE', 'color': 1}
            )
        
        # Add rectangles as polylines
        for idx, rect in enumerate(result.rectangles):
            corners = rect.get_corners()
            points = [(c.x, c.y) for c in corners]
            points.append(points[0])  # Close the polygon
            
            msp.add_lwpolyline(
                points,
                dxfattribs={'layer': f'RECTANGLE_{idx + 1}'}
            )
        
        # Save file
        doc.saveas(test_filename)
        
        # Check file
        if os.path.exists(test_filename):
            file_size = os.path.getsize(test_filename)
            print(f"\n✅ PASSED: DXF export successful")
            print(f"  Filename: {test_filename}")
            print(f"  File size: {file_size:,} bytes")
            print(f"  Elements: {result.count} rectangles + circle")
            
            if file_size == 0:
                print(f"\n⚠️  WARNING: File size is 0 bytes!")
                return False
            
            # Clean up
            os.remove(test_filename)
            return True
        else:
            print(f"\n❌ FAILED: DXF file was not created")
            return False
            
    except Exception as ex:
        import traceback
        print(f"\n❌ FAILED: DXF export error")
        print(f"  Error: {ex}")
        print(f"\nTraceback:")
        print(traceback.format_exc())
        return False

def generate_summary_report(result, tests_passed, tests_failed):
    """Generate a summary report"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(tests_passed) + len(tests_failed)
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {len(tests_passed)} ✅")
    print(f"Failed: {len(tests_failed)} ❌")
    
    if tests_passed:
        print(f"\nPassed Tests:")
        for test_name in tests_passed:
            print(f"  ✅ {test_name}")
    
    if tests_failed:
        print(f"\nFailed Tests:")
        for test_name in tests_failed:
            print(f"  ❌ {test_name}")
    
    print("\n" + "=" * 80)
    
    if not tests_failed:
        print("🎉 ALL TESTS PASSED! 🎉")
    else:
        print("⚠️  SOME TESTS FAILED - SEE DETAILS ABOVE")
    
    print("=" * 80)

def main():
    """Main test function"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  RECTANGLE PACKING - AUTOMATED TEST SUITE (v2)".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    tests_passed = []
    tests_failed = []
    
    # Test 1: Run packing algorithm
    try:
        result = test_packing_algorithm()
        tests_passed.append("Packing Algorithm")
    except Exception as ex:
        import traceback
        print(f"\n❌ FAILED: Packing algorithm crashed")
        print(f"  Error: {ex}")
        print(traceback.format_exc())
        tests_failed.append("Packing Algorithm")
        return
    
    # Test 2: Check rotation angles
    if test_rotation_angles(result):
        tests_passed.append("Rotation Angles")
    else:
        tests_failed.append("Rotation Angles")
    
    # Test 3: Check for overlaps
    if test_overlaps(result, tolerance=0.0):
        tests_passed.append("Overlap Detection")
    else:
        tests_failed.append("Overlap Detection")
    
    # Test 4: Check circle bounds
    if test_circle_bounds(result, circle_diameter=100.0, safe_zone=0.0):
        tests_passed.append("Circle Bounds")
    else:
        tests_failed.append("Circle Bounds")
    
    # Test 5: Test DXF export
    if test_dxf_export(result, circle_diameter=100.0, safe_zone=0.0):
        tests_passed.append("DXF Export")
    else:
        tests_failed.append("DXF Export")
    
    # Generate summary
    generate_summary_report(result, tests_passed, tests_failed)
    
    # Return exit code
    sys.exit(0 if not tests_failed else 1)

if __name__ == "__main__":
    main()
