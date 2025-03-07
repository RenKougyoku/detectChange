import cv2
import numpy as np
import pyautogui
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
from tkinter import messagebox

class RegionSelector:
    def __init__(self, parent):
        self.root = tk.Toplevel(parent)
        self.root.attributes('-alpha', 0.3)  # Make window semi-transparent
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        
        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Variables to store rectangle coordinates
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.region = None
        
        # Create canvas
        self.canvas = tk.Canvas(self.root, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # Bind Escape key to cancel
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        
        # Add instruction text
        self.canvas.create_text(
            self.screen_width // 2,
            50,
            text="Click and drag to select region. Press ESC to cancel.",
            fill="black",
            font=("Arial", 24, "bold")
        )
        print("[RegionSelector] Window created")
        

    def on_press(self, event):
        # Get absolute screen coordinates
        self.start_x = event.x_root
        self.start_y = event.y_root
        print(f"[RegionSelector] Mouse press - Start position: ({self.start_x}, {self.start_y})")

    def on_drag(self, event):
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        
        # Use root coordinates for accurate position
        current_x = event.x_root
        current_y = event.y_root
        
        # Convert to canvas coordinates
        canvas_x1 = self.start_x - self.root.winfo_x()
        canvas_y1 = self.start_y - self.root.winfo_y()
        canvas_x2 = current_x - self.root.winfo_x()
        canvas_y2 = current_y - self.root.winfo_y()
        
        self.current_rect = self.canvas.create_rectangle(
            canvas_x1, canvas_y1, canvas_x2, canvas_y2,
            outline="red", width=2
        )

    def on_release(self, event):
        # Use root coordinates for accurate position
        end_x = event.x_root
        end_y = event.y_root
        
        # Calculate the region coordinates
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        # Store as (x, y, width, height)
        self.region = (x1, y1, x2 - x1, y2 - y1)
        print(f"[RegionSelector] Release - End position: ({end_x}, {end_y})")
        print(f"[RegionSelector] Final region: {self.region}")
        self.root.destroy()

    def get_region(self):
        self.root.wait_window()
        return self.region

class Region:
    def __init__(self, x=100, y=100, width=800, height=600):
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        
    @property
    def x(self):
        return self._x
        
    @x.setter
    def x(self, value):
        self._x = int(value)
        
    @property
    def y(self):
        return self._y
        
    @y.setter
    def y(self, value):
        self._y = int(value)
        
    @property
    def width(self):
        return self._width
        
    @width.setter
    def width(self, value):
        self._width = int(value)
        
    @property
    def height(self):
        return self._height
        
    @height.setter
    def height(self, value):
        self._height = int(value)
        
    def get_coordinates(self):
        """Returns the region coordinates as a list [x, y, width, height]"""
        return [self._x, self._y, self._width, self._height]
        
    def update_from_coordinates(self, coordinates):
        """Update region from a list or tuple of coordinates [x, y, width, height]"""
        print(f"[Region] Updating coordinates from {coordinates}")
        if len(coordinates) != 4:
            raise ValueError("Coordinates must contain exactly 4 values: x, y, width, height")
        
        # Store old values for logging
        old_x, old_y, old_width, old_height = self._x, self._y, self._width, self._height
        
        # Update values
        self._x, self._y, self._width, self._height = coordinates
        
        # Log the changes
        print(f"[Region] Updated: ({old_x}, {old_y}, {old_width}, {old_height}) -> ({self._x}, {self._y}, {self._width}, {self._height})")

    def __str__(self):
        return f"Region(x={self._x}, y={self._y}, width={self._width}, height={self._height})"

class ScreenChangeDetectorUI:
    def __init__(self, root, shared_region):
        self.root = root
        self.root.title("Screen Change Detector")
        
        # Initialize variables
        self.running = False
        self._region = shared_region  # Use the shared region object
        self.threshold = 30
        
        # Create StringVars with traces
        self.x_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        
        # Initialize the region values
        self.initialize_region()
        
        # Add traces to update region when StringVars change
        self.x_var.trace_add("write", self._on_entry_change)
        self.y_var.trace_add("write", self._on_entry_change)
        self.width_var.trace_add("write", self._on_entry_change)
        self.height_var.trace_add("write", self._on_entry_change)
        
        print(f"[ScreenChangeDetectorUI] Initialized with shared region: {self._region}")
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create image labels
        self.img_frame = ttk.Frame(self.main_frame)
        self.img_frame.grid(row=0, column=0, columnspan=2, pady=10)
        
        self.current_label = ttk.Label(self.img_frame, text="Current Image")
        self.current_label.grid(row=0, column=0, padx=5)
        
        self.current_image_label = ttk.Label(self.img_frame)
        self.current_image_label.grid(row=1, column=0, padx=5)
        
        # Controls frame
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Start/Stop button
        self.start_button = ttk.Button(self.control_frame, text="Start", command=self.toggle_monitoring)
        self.start_button.grid(row=0, column=0, padx=5)
        
        # Select Region button
        self.select_region_button = ttk.Button(self.control_frame, text="Select Region", command=self.select_region)
        self.select_region_button.grid(row=0, column=1, padx=5)
        
        # Region settings with proper binding
        self.region_frame = ttk.LabelFrame(self.control_frame, text="Region Settings", padding="5")
        self.region_frame.grid(row=0, column=2, padx=10)
        
        # Create and store Entry widgets as instance variables with trace
        ttk.Label(self.region_frame, text="X:").grid(row=0, column=0)
        self.x_entry = ttk.Entry(self.region_frame, textvariable=self.x_var, width=5)
        self.x_entry.grid(row=0, column=1)
        
        ttk.Label(self.region_frame, text="Y:").grid(row=0, column=2)
        self.y_entry = ttk.Entry(self.region_frame, textvariable=self.y_var, width=5)
        self.y_entry.grid(row=0, column=3)
        
        ttk.Label(self.region_frame, text="Width:").grid(row=0, column=4)
        self.width_entry = ttk.Entry(self.region_frame, textvariable=self.width_var, width=5)
        self.width_entry.grid(row=0, column=5)
        
        ttk.Label(self.region_frame, text="Height:").grid(row=0, column=6)
        self.height_entry = ttk.Entry(self.region_frame, textvariable=self.height_var, width=5)
        self.height_entry.grid(row=0, column=7)
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="Status: Ready")
        self.status_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Change counter
        self.changes_detected = 0
        self.changes_label = ttk.Label(self.main_frame, text="Changes detected: 0")
        self.changes_label.grid(row=3, column=0, columnspan=2)

    def initialize_region(self):
        """Initialize the region values in the UI."""
        self.x_var.set(str(self._region.x))
        self.y_var.set(str(self._region.y))
        self.width_var.set(str(self._region.width))
        self.height_var.set(str(self._region.height))

    def update_region(self, new_coordinates):
        """Update the region with new coordinates."""
        print(f"[ScreenChangeDetectorUI] Attempting to update region with coordinates: {new_coordinates}")
        try:
            self._region.update_from_coordinates(new_coordinates)
            self.initialize_region()  # Update UI with new values
            print(f"[ScreenChangeDetectorUI] Region updated: {self._region}")
        except Exception as e:
            print(f"[ScreenChangeDetectorUI] Error updating region: {e}")

    @property
    def region(self):
        """Returns the region coordinates as a list for compatibility with pyautogui"""
        return self._region.get_coordinates()

    def _on_entry_change(self, *args):
        """Called when any of the entry fields change"""
        try:
            x = int(self.x_var.get())
            y = int(self.y_var.get())
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            self._region.update_from_coordinates([x, y, width, height])
            print(f"[ScreenChangeDetectorUI] Region updated from UI: {self._region}")
            
            # Update preview if not running
            if not self.running:
                initial_capture = self.capture_window()
                if initial_capture is not None:
                    self.update_image_display(initial_capture)
        except (ValueError, TypeError) as e:
            print(f"[ScreenChangeDetectorUI] Invalid entry value: {e}")
            
    def _update_region(self, new_region):
        """Update region and UI values"""
        try:
            # Temporarily remove traces
            self.x_var.trace_remove("write", self.x_var.trace_info()[0][1])
            self.y_var.trace_remove("write", self.y_var.trace_info()[0][1])
            self.width_var.trace_remove("write", self.width_var.trace_info()[0][1])
            self.height_var.trace_remove("write", self.height_var.trace_info()[0][1])
            
            # Update region
            self._region.update_from_coordinates(new_region)
            
            # Update UI
            self.x_var.set(str(self._region.x))
            self.y_var.set(str(self._region.y))
            self.width_var.set(str(self._region.width))
            self.height_var.set(str(self._region.height))
            
            # Force immediate update
            self.root.update_idletasks()
            
            # Re-add traces
            self.x_var.trace_add("write", self._on_entry_change)
            self.y_var.trace_add("write", self._on_entry_change)
            self.width_var.trace_add("write", self._on_entry_change)
            self.height_var.trace_add("write", self._on_entry_change)
            
            print(f"[ScreenChangeDetectorUI] Region updated: {self._region}")
            return True
        except Exception as e:
            print(f"[ScreenChangeDetectorUI] Error updating region: {e}")
            return False

    def update_region_display(self):
        """Update the UI to reflect current region values"""
        try:
            # Update StringVars
            self.x_var.set(str(self._region.x))
            self.y_var.set(str(self._region.y))
            self.width_var.set(str(self._region.width))
            self.height_var.set(str(self._region.height))
            
            # Force update
            self.root.update()
            
            # Take a new screenshot
            if not self.running:
                initial_capture = self.capture_window()
                if initial_capture is not None:
                    self.update_image_display(initial_capture)
                    
            print(f"[ScreenChangeDetectorUI] Display updated with region: {self._region}")
        except Exception as e:
            print(f"[ScreenChangeDetectorUI] Error updating display: {str(e)}")

    def select_region(self):
        if self.running:
            messagebox.showwarning("Warning", "Please stop monitoring before selecting a new region.")
            return
        
        print("[ScreenChangeDetectorUI] Starting region selection")
        print(f"[ScreenChangeDetectorUI] Current region: {self._region}")
        
        # Call the new select_position method
        self.select_position()

    def select_position(self):
        # Minimize the main window
        self.root.iconify()
        time.sleep(0.5)
        
        # Create and show region selector with parent
        selector = RegionSelector(self.root)
        new_region = selector.get_region()
        
        # Restore the main window
        self.root.deiconify()
        
        if new_region:
            print(f"[ScreenChangeDetectorUI] New region selected: {new_region}")
            try:
                # Update the region object directly
                print(f"[ScreenChangeDetectorUI] Before update - Region: {self._region}")
                self._region.update_from_coordinates(new_region)
                print(f"[ScreenChangeDetectorUI] After update - Region: {self._region}")
                
                # Explicitly update each StringVar
                print("[ScreenChangeDetectorUI] Updating UI StringVars...")
                self.x_var.set(str(self._region.x))
                self.y_var.set(str(self._region.y))
                self.width_var.set(str(self._region.width))
                self.height_var.set(str(self._region.height))
                
                # Force update and print current values
                self.root.update_idletasks()
                print(f"[ScreenChangeDetectorUI] StringVar values - X: {self.x_var.get()}, Y: {self.y_var.get()}, Width: {self.width_var.get()}, Height: {self.height_var.get()}")
                
                # Take a new screenshot
                if not self.running:
                    print("[ScreenChangeDetectorUI] Capturing window...")
                    initial_capture = self.capture_window()
                    if initial_capture is not None:
                        print("[ScreenChangeDetectorUI] Updating image display...")
                        self.update_image_display(initial_capture)
                
                self.status_label.config(text="Status: Region selected and ready")
                print("[ScreenChangeDetectorUI] Region selection complete")
            except Exception as e:
                import traceback
                print(f"[ScreenChangeDetectorUI] Error updating region: {str(e)}")
                traceback.print_exc()
                self.status_label.config(text=f"Error: {str(e)}")
        else:
            print("[ScreenChangeDetectorUI] Region selection cancelled")

    def capture_window(self):
        try:
            screenshot = pyautogui.screenshot(region=self.region)
            print(f"[ScreenChangeDetectorUI] Capturing window with region: {self._region}")
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"[ScreenChangeDetectorUI] Screenshot error: {e}")
            self.status_label.config(text=f"Error: {e}")
            return None

    def detect_changes(self, image1, image2):
        if image1 is None or image2 is None:
            return False
        diff = cv2.absdiff(image1, image2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, self.threshold, 255, cv2.THRESH_BINARY)
        return np.count_nonzero(thresh) > 0

    def update_image_display(self, image):
        if image is not None:
            try:
                # Convert BGR to RGB
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                # Resize image to fit in the UI
                display_size = (400, 300)
                image_resized = cv2.resize(image_rgb, display_size)
                # Convert to PhotoImage
                image_pil = Image.fromarray(image_resized)
                image_tk = ImageTk.PhotoImage(image_pil)
                self.current_image_label.configure(image=image_tk)
                self.current_image_label.image = image_tk  # Keep a reference!
                print("[ScreenChangeDetectorUI] Image display updated successfully")
            except Exception as e:
                print(f"[ScreenChangeDetectorUI] Error updating image display: {str(e)}")

    def toggle_monitoring(self):
        if not self.running:
            try:
                print(f"[ScreenChangeDetectorUI] Starting monitoring with region: {self._region}")
                self.running = True
                self.start_button.config(text="Stop")
                self.status_label.config(text="Status: Running")
                threading.Thread(target=self.monitoring_loop, daemon=True).start()
            except Exception as e:
                print(f"[ScreenChangeDetectorUI] Error starting monitoring: {e}")
                self.status_label.config(text="Error: Could not start monitoring")
        else:
            self.running = False
            self.start_button.config(text="Start")
            self.status_label.config(text="Status: Stopped")

    def monitoring_loop(self):
        initial_image = self.capture_window()
        while self.running:
            current_image = self.capture_window()
            if self.detect_changes(initial_image, current_image):
                self.changes_detected += 1
                self.root.after(0, lambda: self.changes_label.config(
                    text=f"Changes detected: {self.changes_detected}"
                ))
            
            self.root.after(0, lambda img=current_image: self.update_image_display(img))
            initial_image = current_image
            time.sleep(1)

def update_shared_region(shared_region, new_coordinates):
    """Update the shared region object with new coordinates"""
    try:
        shared_region.update_from_coordinates(new_coordinates)
        print(f"[Main] Shared region updated: {shared_region}")
        return True
    except Exception as e:
        print(f"[Main] Error updating shared region: {str(e)}")
        return False

def main():
    # Create a single shared Region object
    shared_region = Region(100, 100, 800, 600)
    print(f"[Main] Created shared region: {shared_region}")
    
    # Create the main window
    root = tk.Tk()
    
    # Create the UI with the shared region
    app = ScreenChangeDetectorUI(root, shared_region)
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main()