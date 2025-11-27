#!/usr/bin/env python3
"""
Rechtecke in Kreis - Optimierungs-App mit Modern GUI
Berechnet die optimale Platzierung von Rechtecken in einem Kreis
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import math
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw
import ezdxf

# Importiere die Kern-Logik (ohne GUI-Abhängigkeiten)
from packing_logic import RectanglePacker, PackingResult, Rectangle


class RectanglesInCircleApp:
    """Hauptanwendung mit Modern GUI"""

    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Rechtecke in Kreis - Optimierer")
        self.root.geometry("1200x800")

        # Set theme
        ctk.set_appearance_mode("dark")  # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

        self.current_result: Optional[PackingResult] = None
        # For hover tooltips
        self.hover_label: Optional[ctk.CTkLabel] = None
        self.rectangle_bounds: List[Tuple[int, int, int, int, int]] = []  # (x1, y1, x2, y2, rect_id)

        self._create_widgets()

        # Initiale Berechnung
        self.root.after(100, self.calculate)

    def _create_widgets(self):
        """Erstellt die GUI-Elemente"""
        # Hauptcontainer
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure grid
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Linke Seite - Eingaben
        left_frame = ctk.CTkFrame(main_frame, width=350)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.grid_propagate(False)

        # Titel + Dark Mode Toggle
        header_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 20), padx=10)
        
        title_label = ctk.CTkLabel(header_frame, text="Einstellungen", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(side="left")
        
        # Dark mode toggle
        self.appearance_mode_var = ctk.StringVar(value="dark")
        dark_mode_switch = ctk.CTkSwitch(
            header_frame, 
            text="Dark Mode On", 
            command=self.toggle_appearance_mode,
            variable=self.appearance_mode_var,
            onvalue="dark",
            offvalue="light"
        )
        dark_mode_switch.pack(side="right")
        dark_mode_switch.select()
        self.dark_mode_switch = dark_mode_switch  # Store reference for later updates

        # Input container
        input_container = ctk.CTkFrame(left_frame, fg_color="transparent")
        input_container.pack(fill="x", padx=10, pady=(0, 10))

        # Kreisdurchmesser
        ctk.CTkLabel(input_container, text="Kreisdurchmesser (mm):", anchor="w").pack(fill="x", pady=(5, 2))
        self.circle_diameter_var = ctk.StringVar(value="100")
        ctk.CTkEntry(input_container, textvariable=self.circle_diameter_var).pack(fill="x", pady=(0, 10))

        # Rechteck Breite
        ctk.CTkLabel(input_container, text="Rechteck Breite (mm):", anchor="w").pack(fill="x", pady=(5, 2))
        self.rect_width_var = ctk.StringVar(value="15")
        ctk.CTkEntry(input_container, textvariable=self.rect_width_var).pack(fill="x", pady=(0, 10))

        # Rechteck Höhe
        ctk.CTkLabel(input_container, text="Rechteck Höhe (mm):", anchor="w").pack(fill="x", pady=(5, 2))
        self.rect_height_var = ctk.StringVar(value="10")
        ctk.CTkEntry(input_container, textvariable=self.rect_height_var).pack(fill="x", pady=(0, 10))

        # Toleranz (NEU)
        ctk.CTkLabel(input_container, text="Toleranz/Abstand (mm):", anchor="w").pack(fill="x", pady=(5, 2))
        self.tolerance_var = ctk.StringVar(value="0")
        ctk.CTkEntry(input_container, textvariable=self.tolerance_var).pack(fill="x", pady=(0, 10))

        # Safe Zone (NEU)
        ctk.CTkLabel(input_container, text="Sicherheitszone Rand (mm):", anchor="w").pack(fill="x", pady=(5, 2))
        self.safe_zone_var = ctk.StringVar(value="0")
        ctk.CTkEntry(input_container, textvariable=self.safe_zone_var).pack(fill="x", pady=(0, 10))

        # Berechnen Button
        calc_button = ctk.CTkButton(
            input_container, 
            text="Berechnen", 
            command=self.calculate,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        calc_button.pack(fill="x", pady=(10, 20))

        # Export Buttons
        export_frame = ctk.CTkFrame(input_container, fg_color="transparent")
        export_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(
            export_frame, 
            text="📄 Export PNG", 
            command=self.export_to_png,
            height=35
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            export_frame, 
            text="📐 Export DXF", 
            command=self.export_to_dxf,
            height=35
        ).pack(fill="x", pady=2)

        # Ergebnis-Bereich
        result_frame = ctk.CTkFrame(left_frame)
        result_frame.pack(fill="both", expand=True, pady=(10, 10), padx=10)

        result_label = ctk.CTkLabel(result_frame, text="Ergebnis", font=ctk.CTkFont(size=18, weight="bold"))
        result_label.pack(pady=(10, 5))

        self.result_text = ctk.CTkTextbox(result_frame, height=200, font=ctk.CTkFont(size=12))
        self.result_text.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Rechte Seite - Canvas
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")

        canvas_label = ctk.CTkLabel(right_frame, text="Visualisierung", font=ctk.CTkFont(size=18, weight="bold"))
        canvas_label.pack(pady=(10, 5))

        # Canvas in a frame
        canvas_frame = ctk.CTkFrame(right_frame)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Create canvas using tkinter Canvas (CustomTkinter doesn't have a Canvas widget)
        import tkinter as tk
        self.canvas = tk.Canvas(canvas_frame, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Bind resize and motion events
        self.canvas.bind("<Configure>", lambda e: self.draw_result())
        self.canvas.bind("<Motion>", self.on_canvas_hover)
        
        # Create hover tooltip label (initially hidden)
        self.hover_label = ctk.CTkLabel(
            self.canvas, 
            text="", 
            fg_color=("gray90", "gray20"),
            corner_radius=5,
            font=ctk.CTkFont(size=11)
        )

    def toggle_appearance_mode(self):
        """Toggle between dark and light mode"""
        if self.appearance_mode_var.get() == "dark":
            ctk.set_appearance_mode("dark")
            self.canvas.configure(bg="#2b2b2b")
            self.dark_mode_switch.configure(text="Dark Mode On")
        else:
            ctk.set_appearance_mode("light")
            self.canvas.configure(bg="#f0f0f0")
            self.dark_mode_switch.configure(text="Dark Mode Off")
        self.draw_result()

    def calculate(self):
        """Führt die Berechnung durch"""
        try:
            # Parse Eingabewerte
            circle_diameter = float(self.circle_diameter_var.get())
            rect_width = float(self.rect_width_var.get())
            rect_height = float(self.rect_height_var.get())
            tolerance = float(self.tolerance_var.get())
            safe_zone = float(self.safe_zone_var.get())

            # Validierung
            if circle_diameter <= 0 or rect_width <= 0 or rect_height <= 0:
                messagebox.showerror("Fehler", "Alle Werte müssen größer als 0 sein!")
                return
            
            if tolerance < 0 or safe_zone < 0:
                messagebox.showerror("Fehler", "Toleranz und Sicherheitszone können nicht negativ sein!")
                return

            # Berechnung durchführen
            packer = RectanglePacker(circle_diameter, rect_width, rect_height, tolerance, safe_zone)
            self.current_result = packer.find_optimal_packing()

            # Ergebnis anzeigen
            result_text = (
                f"✓ Anzahl Rechtecke: {self.current_result.count}\n\n"
                f"📏 Kreisdurchmesser: {circle_diameter:.2f} mm\n"
                f"   Kreisradius: {circle_diameter / 2:.2f} mm\n"
                f"   Effektiver Radius: {circle_diameter / 2 - safe_zone:.2f} mm\n\n"
                f"📐 Rechteck Breite: {rect_width:.2f} mm\n"
                f"   Rechteck Höhe: {rect_height:.2f} mm\n\n"
                f"⚙️ Toleranz/Abstand: {tolerance:.2f} mm\n"
                f"   Sicherheitszone: {safe_zone:.2f} mm\n\n"
                f"📊 Effizienz: {self.current_result.efficiency:.2f}%\n"
                f"   Verschwendung: {self.current_result.waste:.2f}%\n"
                f"   Genutzte Fläche: {self.current_result.used_area:.2f} mm²\n"
                f"   Gesamtfläche: {self.current_result.total_area:.2f} mm²\n\n"
                f"🎯 Beste Strategie:\n   {self.current_result.strategy}"
            )

            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", result_text)

            # Zeichnung aktualisieren
            self.draw_result()

        except ValueError:
            messagebox.showerror("Fehler", "Bitte geben Sie gültige Zahlenwerte ein!")
        except Exception as ex:
            messagebox.showerror("Fehler", f"Fehler bei der Berechnung: {ex}")

    def draw_result(self):
        """Zeichnet das Ergebnis auf dem Canvas"""
        self.canvas.delete("all")
        self.rectangle_bounds.clear()

        if self.current_result is None or self.current_result.circle is None:
            return

        # Canvas-Dimensionen
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return

        # Berechne Skalierung
        diameter = self.current_result.circle.radius * 2
        scale = min(canvas_width, canvas_height) / diameter * 0.85

        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # Colors based on theme
        is_dark = self.appearance_mode_var.get() == "dark"
        circle_color = "#404040" if is_dark else "#d0d0d0"
        circle_outline = "#606060" if is_dark else "#404040"
        rect_fill = "#3b8ed0" if is_dark else "#5fa3d9"
        rect_outline = "#1f6aa5" if is_dark else "#3a7ca5"
        text_color = "#ffffff" if is_dark else "#000000"
        
        # Draw safe zone if present
        safe_zone = float(self.safe_zone_var.get())
        if safe_zone > 0:
            safe_radius_scaled = (self.current_result.circle.radius - safe_zone) * scale
            self.canvas.create_oval(
                center_x - safe_radius_scaled,
                center_y - safe_radius_scaled,
                center_x + safe_radius_scaled,
                center_y + safe_radius_scaled,
                outline="#ff6b6b",
                width=2,
                dash=(5, 5)
            )

        # Zeichne Kreis
        circle_radius_scaled = self.current_result.circle.radius * scale
        self.canvas.create_oval(
            center_x - circle_radius_scaled,
            center_y - circle_radius_scaled,
            center_x + circle_radius_scaled,
            center_y + circle_radius_scaled,
            outline=circle_outline,
            width=2,
            fill=circle_color
        )

        # Zeichne Rechtecke
        for idx, rect in enumerate(self.current_result.rectangles):
            self._draw_rectangle(rect, idx, scale, center_x, center_y, rect_fill, rect_outline)

        # Zeichne Beschriftung
        self.canvas.create_text(
            10, 10,
            text=f"{self.current_result.count} Rechtecke | {self.current_result.efficiency:.1f}% Effizienz",
            anchor="nw",
            font=("Arial", 14, "bold"),
            fill=text_color
        )

        # Weitere Infos
        info_text = (
            f"Kreis: Ø {diameter:.1f} mm\n"
            f"Rechteck: {self.current_result.rectangles[0].width:.1f} × "
            f"{self.current_result.rectangles[0].height:.1f} mm\n"
            f"Strategie: {self.current_result.strategy}"
        )
        self.canvas.create_text(
            10, 40,
            text=info_text,
            anchor="nw",
            font=("Arial", 10),
            fill=text_color
        )

    def _draw_rectangle(self, rect: Rectangle, rect_id: int, scale: float, 
                       center_x: float, center_y: float, fill_color: str, outline_color: str):
        """Zeichnet ein einzelnes Rechteck"""
        corners = rect.get_corners()

        # Konvertiere zu Canvas-Koordinaten
        points = []
        for corner in corners:
            x = center_x + corner.x * scale
            y = center_y + corner.y * scale
            points.extend([x, y])

        # Store bounds for hover detection (and store rect for center marker)
        xs = [points[i] for i in range(0, len(points), 2)]
        ys = [points[i] for i in range(1, len(points), 2)]
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        self.rectangle_bounds.append((int(x1), int(y1), int(x2), int(y2), rect_id))

        self.canvas.create_polygon(
            points,
            outline=outline_color,
            width=1,
            fill=fill_color,
            tags=f"rect_{rect_id}"
        )
    
    def _draw_center_marker(self, rect: Rectangle):
        """Draws a visual marker at the center of a rectangle when hovering"""
        if self.current_result is None:
            return
        
        # Canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # Calculate scale and center
        diameter = self.current_result.circle.radius * 2
        scale = min(canvas_width, canvas_height) / diameter * 0.85
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # Convert rectangle center to canvas coordinates
        marker_x = center_x + rect.position.x * scale
        marker_y = center_y + rect.position.y * scale
        
        # Draw crosshair marker
        marker_size = 6
        is_dark = self.appearance_mode_var.get() == "dark"
        marker_color = "#ff6b6b" if is_dark else "#e74c3c"
        
        # Crosshair lines
        self.canvas.create_line(
            marker_x - marker_size, marker_y,
            marker_x + marker_size, marker_y,
            fill=marker_color,
            width=2,
            tags="center_marker"
        )
        self.canvas.create_line(
            marker_x, marker_y - marker_size,
            marker_x, marker_y + marker_size,
            fill=marker_color,
            width=2,
            tags="center_marker"
        )
        # Center dot
        self.canvas.create_oval(
            marker_x - 2, marker_y - 2,
            marker_x + 2, marker_y + 2,
            fill=marker_color,
            outline=marker_color,
            tags="center_marker"
        )

    def on_canvas_hover(self, event):
        """Handle mouse hover over canvas to show rectangle info"""
        # Remove any existing center marker
        self.canvas.delete("center_marker")
        
        if not self.rectangle_bounds:
            self.hover_label.place_forget()
            return

        # Check if mouse is over any rectangle
        for x1, y1, x2, y2, rect_id in self.rectangle_bounds:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                rect = self.current_result.rectangles[rect_id]
                
                # Update tooltip with clarification that position is the center
                tooltip_text = (
                    f"Rechteck #{rect_id + 1}\n"
                    f"Zentrum: ({rect.position.x:.1f}, {rect.position.y:.1f}) mm\n"
                    f"Rotation: {rect.rotation:.0f}°"
                )
                self.hover_label.configure(text=tooltip_text)
                # Position tooltip near mouse
                self.hover_label.place(x=event.x + 10, y=event.y + 10)
                
                # Draw visual center point indicator
                self._draw_center_marker(rect)
                return

        # No rectangle under mouse
        self.hover_label.place_forget()

    def export_to_png(self):
        """Export visualization as PNG"""
        if self.current_result is None:
            messagebox.showwarning("Warnung", "Bitte führen Sie zuerst eine Berechnung durch!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )

        if not filename:
            return

        try:
            # Create image
            img_size = 2000  # High resolution
            img = Image.new('RGB', (img_size, img_size), color='white')
            draw = ImageDraw.Draw(img)

            center = img_size / 2
            diameter = self.current_result.circle.radius * 2
            scale = img_size / diameter * 0.85

            # Draw circle
            radius_scaled = self.current_result.circle.radius * scale
            draw.ellipse(
                [center - radius_scaled, center - radius_scaled, 
                 center + radius_scaled, center + radius_scaled],
                outline='black',
                width=3,
                fill='#f0f0f0'
            )

            # Draw safe zone if present
            safe_zone = float(self.safe_zone_var.get())
            if safe_zone > 0:
                safe_radius_scaled = (self.current_result.circle.radius - safe_zone) * scale
                draw.ellipse(
                    [center - safe_radius_scaled, center - safe_radius_scaled,
                     center + safe_radius_scaled, center + safe_radius_scaled],
                    outline='red',
                    width=2
                )

            # Draw rectangles
            for rect in self.current_result.rectangles:
                corners = rect.get_corners()
                points = []
                for corner in corners:
                    x = center + corner.x * scale
                    y = center + corner.y * scale
                    points.append((x, y))

                draw.polygon(points, outline='darkblue', fill='lightblue', width=2)

            img.save(filename)
            messagebox.showinfo("Erfolg", f"PNG erfolgreich exportiert:\n{filename}")

        except Exception as ex:
            messagebox.showerror("Fehler", f"Fehler beim PNG-Export: {ex}")

    def export_to_dxf(self):
        """Export design as DXF for CAD"""
        if self.current_result is None:
            messagebox.showwarning("Warnung", "Bitte führen Sie zuerst eine Berechnung durch!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".dxf",
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")]
        )

        if not filename:
            return

        try:
            import os
            
            # Create DXF document
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()

            # Add circle
            msp.add_circle(
                center=(0, 0),
                radius=self.current_result.circle.radius,
                dxfattribs={'layer': 'CIRCLE'}
            )

            # Add safe zone if present
            safe_zone = float(self.safe_zone_var.get())
            if safe_zone > 0:
                msp.add_circle(
                    center=(0, 0),
                    radius=self.current_result.circle.radius - safe_zone,
                    dxfattribs={'layer': 'SAFE_ZONE', 'color': 1}  # Red
                )

            # Add rectangles as polylines
            for idx, rect in enumerate(self.current_result.rectangles):
                corners = rect.get_corners()
                points = [(c.x, c.y) for c in corners]
                points.append(points[0])  # Close the polygon
                
                msp.add_lwpolyline(
                    points,
                    dxfattribs={'layer': f'RECTANGLE_{idx + 1}'}
                )

            # Save with explicit error checking
            doc.saveas(filename)
            
            # Verify file was created and has content
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                if file_size > 0:
                    messagebox.showinfo("Erfolg", 
                        f"DXF erfolgreich exportiert:\\n{filename}\\n\\n"
                        f"Dateigröße: {file_size:,} bytes\\n"
                        f"Elemente: {len(self.current_result.rectangles)} Rechtecke + Kreis")
                else:
                    raise Exception("DXF-Datei wurde erstellt, ist aber leer (0 bytes)")
            else:
                raise Exception("DXF-Datei konnte nicht erstellt werden")

        except Exception as ex:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror("Fehler", 
                f"Fehler beim DXF-Export:\\n{str(ex)}\\n\\n"
                f"Details:\\n{error_details[:500]}")


def main():
    """Hauptfunktion"""
    root = ctk.CTk()
    RectanglesInCircleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
