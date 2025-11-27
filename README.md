# Rectangles in Circle - Optimization App

A professional rectangle packing application that optimally places rectangles within a circular boundary using advanced algorithms and modern UI.

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production-brightgreen.svg)

## Features

✨ **Modern Dark Mode UI** - Professional appearance with dynamic dark/light mode toggle  
🎯 **Systematic Gap Filling** - Intelligently fills empty spaces after grid placement  
🔒 **Guaranteed Overlap-Free** - SAT (Separating Axis Theorem) collision detection  
📊 **Real-time Efficiency Metrics** - Live packing efficiency and waste percentage  
📐 **CAD Export** - Export to DXF format for manufacturing  
🖼️ **PNG Export** - High-resolution visualization export  
💡 **Interactive Tooltips** - Hover to see rectangle details with visual center markers  
⚙️ **Flexible Parameters** - Tolerance spacing and safety zone support  

## Quick Start

### Requirements

- Python 3.7+
- Required packages (install with pip):

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `customtkinter` - Modern UI components
- `Pillow` - Image export functionality
- `ezdxf` - DXF file export for CAD

### Run the Application

```bash
python rectangles_in_circle.py
```

## Usage

1. **Enter Parameters:**
   - Circle diameter (mm)
   - Rectangle width and height (mm)
   - Optional: Tolerance/spacing (mm)
   - Optional: Safety zone from edge (mm)

2. **Calculate** - Click "Berechnen" to find optimal packing

3. **View Results:**
   - Visualization shows all placed rectangles
   - Hover over rectangles to see position (center point marked with crosshair)
   - Efficiency metrics displayed in result panel

4. **Export:**
   - **PNG** - High-resolution image (2000×2000px)
   - **DXF** - CAD-compatible format for manufacturing

## Packing Algorithm

### Grid Placement + Systematic Gap Filling

1. **Initial Grid** - Places rectangles in optimal grid pattern (0° or 90°)
2. **Systematic Scanning** - Scans entire circle with fine-grained grid to fill empty spaces
3. **Validation** - Ensures no overlaps using SAT collision detection
4. **Optimization** - Tests multiple grid offsets to maximize rectangle count

### Overlap Detection

Uses **Separating Axis Theorem (SAT)**:
- Precise collision detection for rotated rectangles
- Special handling for tolerance=0 (allows edge touching)
- Gap-based calculation for accurate separation measurement

## Code Structure

```
RectanglesInCircle/
├── packing_logic.py          # Core packing algorithm (GUI-independent)
├── rectangles_in_circle.py   # Main application with CustomTkinter UI
├── test.py                   # Comprehensive test suite
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

### Core Modules

**`packing_logic.py`** - Algorithm implementation:
- `Position`, `Circle`, `Rectangle` - Data structures
- `RectanglePacker` - Main optimization class
- SAT collision detection functions
- Systematic gap filling algorithm

**`rectangles_in_circle.py`** - GUI application:
- Modern dark/light mode interface
- Real-time visualization
- Interactive hover tooltips
- Export functionality (PNG, DXF)

**`test.py`** - Automated testing:
- Packing algorithm validation
- Rotation angle verification (0° and 90° only)
- Overlap detection testing
- Circle bounds validation
- DXF export verification

## Testing

Run the comprehensive test suite:

```bash
python test.py
```

**Tests performed:**
1. ✅ Packing Algorithm - Verifies successful packing
2. ✅ Rotation Angles - Ensures only 0° and 90° used
3. ✅ Overlap Detection - Validates no overlaps exist
4. ✅ Circle Bounds - Confirms all rectangles within circle
5. ✅ DXF Export - Tests file creation and validity

## Example Results

### Standard Case (100mm circle, 15×10mm rectangles)
- **Count**: ~40 rectangles
- **Efficiency**: ~76%
- **Strategy**: Strict Grid (0°) + Systematic Gap Fill

### Wide Rectangles (100mm circle, 50×10mm rectangles)
- **Count**: 11-13 rectangles
- **Efficiency**: 70-82%
- **Gaps filled**: Top and bottom curved areas

## Programmatic Usage

Use the packing logic in your own code:

```python
from packing_logic import RectanglePacker

# Create packer with parameters
packer = RectanglePacker(
    circle_diameter=100,
    rect_width=15,
    rect_height=10,
    tolerance=0,      # Space between rectangles
    safe_zone=0       # Distance from circle edge
)

# Find optimal packing
result = packer.find_optimal_packing()

# Access results
print(f"Rectangles placed: {result.count}")
print(f"Efficiency: {result.efficiency:.2f}%")
print(f"Strategy: {result.strategy}")

# Iterate through rectangles
for idx, rect in enumerate(result.rectangles):
    print(f"Rectangle {idx+1}:")
    print(f"  Center: ({rect.position.x:.2f}, {rect.position.y:.2f}) mm")
    print(f"  Rotation: {rect.rotation}°")
```

## Features in Detail

### Tolerance & Safe Zone

**Tolerance** - Minimum spacing between rectangles:
- `tolerance=0` - Rectangles can touch edge-to-edge
- `tolerance>0` - Enforces minimum gap between all rectangles

**Safe Zone** - Minimum distance from circle edge:
- Useful for manufacturing constraints
- All rectangles placed within (radius - safe_zone)

### Center Point Visualization

When hovering over rectangles:
- Tooltip shows "Zentrum" (center point) coordinates
- Red crosshair marker appears at exact center
- Clarifies reference point for all position measurements

### Dark Mode

- Toggle in top-right corner
- Shows "Dark Mode On" or "Dark Mode Off"
- Adapts all colors including canvas and markers

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`, install dependencies:

```bash
pip install customtkinter pillow ezdxf
```

### DXF Export Issues

- Ensure `ezdxf` is installed
- Check file permissions in save location
- Verify sufficient disk space

### Performance with Many Rectangles

For >100 rectangles, calculation may take a few seconds due to systematic scanning. This is normal and ensures optimal gap filling.

## Use Cases

- **Manufacturing** - Optimize material usage on circular workpieces
- **Laser Cutting** - Maximize parts from round stock
- **Packaging** - Fit maximum items in circular containers
- **Production Planning** - Calculate cutting patterns
- **Education** - Visualize packing algorithms

## License

MIT License - Feel free to use and modify

## Contributing

Contributions welcome! Please:
1. Test changes with `test.py`
2. Ensure no overlaps in results
3. Maintain code style

## Version History

**v2.0** (Current)
- Systematic gap filling algorithm
- Modern CustomTkinter UI
- Dark mode support
- DXF/PNG export
- Interactive tooltips with center markers
- Comprehensive test suite

**v1.0** 
- Initial grid-based packing
- Basic Tkinter UI
- SAT collision detection
