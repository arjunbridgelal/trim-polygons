import tkinter as tk
from tkinter import filedialog, messagebox
import geopandas as gpd
from shapely.geometry import shape
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

FONT_LARGE = ("Arial", 14)
FONT_MEDIUM = ("Arial", 12)

class PolygonTrimmerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Polygon Overlap Trimmer")
        self.poly1 = None
        self.poly2 = None
        self.geo1 = None
        self.geo2 = None
        self.trimmed = None
        self.highlight_overlap = None

        self.trim_choice = tk.StringVar(value="Polygon 1")
        self.show_overlap = tk.BooleanVar(value=True)

        self.setup_ui()

    def setup_ui(self):
        input_frame = tk.Frame(self.root, padx=10, pady=10)
        input_frame.pack(side=tk.TOP, fill=tk.X)

        # Row of controls
        tk.Button(input_frame, text="Choose File 1", command=self.load_file1, font=FONT_MEDIUM, bg="#6A0DAD", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(input_frame, text="Choose File 2", command=self.load_file2, font=FONT_MEDIUM, bg="#6A0DAD", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Label(input_frame, text="Trim:", font=FONT_MEDIUM).pack(side=tk.LEFT, padx=(15, 2))
        tk.OptionMenu(input_frame, self.trim_choice, "Polygon 1", "Polygon 2").pack(side=tk.LEFT, padx=5)

        tk.Checkbutton(input_frame, text="Show Overlap", variable=self.show_overlap, font=FONT_MEDIUM).pack(side=tk.LEFT, padx=10)

        tk.Button(input_frame, text="Preview Trim", command=self.preview, font=FONT_LARGE, bg="#FF6F61", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(input_frame, text="Export", command=self.export, font=FONT_LARGE, bg="#228B22", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(input_frame, text="Reset", command=self.reset, font=FONT_LARGE, bg="#001F3F", fg="white").pack(side=tk.LEFT, padx=5)

        # Plot preview and toolbar
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.ax.set_title("Polygon Preview", fontsize=16)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, self.root)
        toolbar.update()
        self.canvas._tkcanvas.pack(fill=tk.BOTH, expand=True)

    def load_file1(self):
        file_path = filedialog.askopenfilename(filetypes=[("GeoJSON Files", "*.geojson"), ("JSON Files", "*.json")])
        if file_path:
            with open(file_path) as f:
                self.geo1 = json.load(f)
                self.poly1 = shape(self.geo1["features"][0]["geometry"])
            self.update_plot()

    def load_file2(self):
        file_path = filedialog.askopenfilename(filetypes=[("GeoJSON Files", "*.geojson"), ("JSON Files", "*.json")])
        if file_path:
            with open(file_path) as f:
                self.geo2 = json.load(f)
                self.poly2 = shape(self.geo2["features"][0]["geometry"])
            self.update_plot()

    def preview(self):
        if not self.poly1 or not self.poly2:
            messagebox.showerror("Error", "Please load both polygons.")
            return

        if not self.poly1.intersects(self.poly2):
            messagebox.showinfo("No Overlap", "Polygons do not overlap.")
            return

        overlap = self.poly1.intersection(self.poly2)
        self.highlight_overlap = overlap if self.show_overlap.get() else None

        if self.trim_choice.get() == "Polygon 1":
            self.trimmed = self.poly1.difference(overlap)
        else:
            self.trimmed = self.poly2.difference(overlap)

        self.update_plot()

    def export(self):
        if not self.trimmed:
            messagebox.showerror("Error", "No trimmed polygon to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".geojson", filetypes=[("GeoJSON Files", "*.geojson"), ("JSON Files", "*.json")])
        if not file_path:
            return

        if self.trim_choice.get() == "Polygon 1":
            original_geo = self.geo1
        else:
            original_geo = self.geo2

        export_geo = json.loads(json.dumps(original_geo))  # Deep copy

        trimmed_geom_json = json.loads(gpd.GeoSeries([self.trimmed]).to_json())["features"][0]["geometry"]
        export_geo["features"][0]["geometry"] = trimmed_geom_json

        # Compact export, like original file
        with open(file_path, "w") as f:
            json.dump(export_geo, f, separators=(',', ':'))

        messagebox.showinfo("Exported", f"Trimmed polygon saved to:\n{file_path}")

    def reset(self):
        self.poly1 = None
        self.poly2 = None
        self.geo1 = None
        self.geo2 = None
        self.trimmed = None
        self.highlight_overlap = None
        self.trim_choice.set("Polygon 1")
        self.show_overlap.set(True)
        self.ax.clear()
        self.ax.set_title("Polygon Preview", fontsize=16)
        self.canvas.draw()
        messagebox.showinfo("Reset", "All data cleared.")

    def update_plot(self):
        self.ax.clear()
        if self.poly1:
            gpd.GeoSeries(self.poly1).plot(ax=self.ax, color="#008080", alpha=0.5, edgecolor="black", label="Polygon 1")
        if self.poly2:
            gpd.GeoSeries(self.poly2).plot(ax=self.ax, color="#FF6F61", alpha=0.5, edgecolor="black", label="Polygon 2")
        if self.highlight_overlap:
            gpd.GeoSeries(self.highlight_overlap).plot(ax=self.ax, color="#DA70D6", alpha=0.7, edgecolor="black", label="Overlap")
        if self.trimmed:
            gpd.GeoSeries(self.trimmed).plot(ax=self.ax, color="#FFC107", alpha=0.7, edgecolor="black", label="Trimmed")
        self.ax.set_title("Polygon Preview", fontsize=16)
        self.ax.legend(fontsize=12)
        self.ax.axis("equal")
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = PolygonTrimmerApp(root)
    root.mainloop()
