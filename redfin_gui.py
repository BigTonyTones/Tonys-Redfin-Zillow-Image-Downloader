import subprocess
import sys

# Check and potentially install dependencies
def check_dependencies():
    """Check for missing packages and ask user for permission to install."""
    required_packages = ['requests', 'beautifulsoup4', 'Pillow']
    missing = []
    
    for package in required_packages:
        try:
            if package == 'Pillow':
                __import__('PIL')
            else:
                __import__(package if package != 'beautifulsoup4' else 'bs4')
        except ImportError:
            missing.append(package)
            
    if missing:
        import tkinter as tk
        from tkinter import messagebox
        import sys
        
        # We need a temporary root to show the messagebox
        temp_root = tk.Tk()
        temp_root.withdraw()
        
        msg = f"The following dependencies are missing: {', '.join(missing)}.\n\nWould you like to install them now?"
        if messagebox.askyesno("Install Dependencies", msg):
            print("Installing dependencies...")
            for package in missing:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to install {package}: {e}")
            messagebox.showinfo("Success", "Dependencies installed successfully! Please restart the application.")
            temp_root.destroy()
            sys.exit(0)
        else:
            messagebox.showwarning("Warning", "The application may not function correctly without these dependencies.")
        temp_root.destroy()

# Check dependencies before full import and GUI startup
check_dependencies()

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin, urlparse
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageTk
import glob

class RedfinDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.version = "1.8.3"
        
        # Performance & DPI Optimizations for Windows
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
            
        # Optimize Tcl performance
        self.root.tk.call('tk', 'scaling', 1.33) # Match standard 96dpi scaling
        
        self.root.title(f"Tonys Real Estate Image Downloader v{self.version}")
        self.root.geometry("1400x900")
        
        # Color Palette - Refined Dark Theme (matching reference)
        self.colors = {
            'bg': '#2b2d31',           # Main background - darker
            'fg': '#dbdee1',           # Primary text - lighter
            'accent': '#5865f2',       # Accent blue - more vibrant
            'accent_hover': '#4752c4', # Hover state
            'card_bg': '#1e1f22',      # Card/panel background - darker
            'border': '#3f4147',       # Borders - subtle
            'text_dim': '#949ba4',     # Secondary text
            'success': '#3ba55d',      # Success/checkmark green
            'hover_bg': '#35373c'      # Hover background
        }
        
        self.output_folder = "House_Images"
        self.current_property = None
        self.current_images = []
        self.gallery_thumbnails = []
        self.photo_references = []
        self.thumbnail_size = 400
        self.thumbnail_cache = {}
        self.property_details = {}  # Store property details (price, beds, baths, etc.)
        self.download_cancelled = False
        
        self.setup_styles()
        self.setup_ui()
        self.refresh_properties()
        
        # Check for updates on startup
        self.check_for_updates()
        
    def setup_styles(self):
        """Initialize custom premium styles."""
        self.root.configure(bg=self.colors['bg'])
        style = ttk.Style()
        
        # Set theme to 'clam' as base for better customization
        try:
            style.theme_use('clam')
        except:
            pass
            
        # General Frame styling
        style.configure("TFrame", background=self.colors['bg'])
        style.configure("Card.TFrame", background=self.colors['card_bg'], relief="flat")
        
        # LabelFrame styling
        style.configure("TLabelframe", background=self.colors['bg'], foreground=self.colors['fg'], bordercolor=self.colors['border'])
        style.configure("TLabelframe.Label", background=self.colors['bg'], foreground=self.colors['accent'], font=("Segoe UI", 10, "bold"))
        
        # Label styling
        style.configure("TLabel", background=self.colors['bg'], foreground=self.colors['fg'], font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=self.colors['bg'], foreground=self.colors['fg'], font=("Segoe UI", 16, "bold"))
        style.configure("Sub.TLabel", background=self.colors['bg'], foreground=self.colors['text_dim'], font=("Segoe UI", 9))
        
        # Button styling - More refined
        style.configure("TButton", 
                        background=self.colors['accent'], 
                        foreground="white", 
                        borderwidth=0, 
                        focuscolor="none",
                        font=("Segoe UI", 9, "bold"),
                        padding=(12, 6),
                        relief="flat")
        style.map("TButton", 
                  background=[('active', self.colors['accent_hover']), ('disabled', '#3f4147')],
                  foreground=[('disabled', '#6d6f78')])
        
        # Entry styling
        style.configure("TEntry", 
                        fieldbackground=self.colors['card_bg'], 
                        foreground=self.colors['fg'],
                        insertcolor='white',
                        borderwidth=1,
                        relief="flat")
        
        # PanedWindow styling
        style.configure("TPanedwindow", background=self.colors['border'])
        
        # Scrollbar styling (dark)
        style.configure("Vertical.TScrollbar", 
                        background=self.colors['card_bg'], 
                        troughcolor=self.colors['bg'],
                        bordercolor=self.colors['border'],
                        arrowcolor=self.colors['fg'])
        
        # Progressbar
        style.configure("Horizontal.TProgressbar", 
                        background=self.colors['accent'], 
                        troughcolor=self.colors['card_bg'],
                        borderwidth=0)
        
        # Exit Button Styling (Red) - Refined
        style.configure("Exit.TButton", 
                        background="#da373c", 
                        foreground="white", 
                        borderwidth=0, 
                        font=("Segoe UI", 9, "bold"),
                        padding=(12, 6),
                        relief="flat")
        style.map("Exit.TButton", 
                  background=[('active', '#a12d32'), ('disabled', '#3f4147')])
        
        # New Treeview Styling (Explorer style)
        style.configure("Treeview", 
                        background=self.colors['card_bg'], 
                        foreground=self.colors['fg'],
                        fieldbackground=self.colors['card_bg'],
                        borderwidth=0,
                        font=("Segoe UI", 10),
                        rowheight=35)
        style.map("Treeview", 
                  background=[('selected', self.colors['accent'])],
                  foreground=[('selected', 'white')])
        
        style.configure("Treeview.Heading", 
                        background=self.colors['bg'], 
                        foreground=self.colors['accent'], 
                        font=("Segoe UI", 9, "bold"),
                        borderwidth=0)
        
    def setup_ui(self):
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Two-pane window
        main_paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Left panel - Download & Explorer
        left_frame = ttk.Frame(main_paned, padding=12)
        main_paned.add(left_frame, weight=1)
        
        # Right panel - Gallery Viewer
        right_frame = ttk.Frame(main_paned, padding=12)
        main_paned.add(right_frame, weight=5)
        
        # === LEFT PANEL ===
        
        # Title/Logo area
        logo_label = ttk.Label(left_frame, text="TONYS IMAGE DOWNLOADER", font=("Segoe UI Black", 13), foreground=self.colors['fg'])
        logo_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Subtitle
        subtitle_label = ttk.Label(left_frame, text="Redfin & Zillow", font=("Segoe UI", 9), foreground=self.colors['text_dim'])
        subtitle_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Download section
        download_section = ttk.Frame(left_frame)
        download_section.pack(fill=tk.X, pady=(0, 25))
        
        self.url_entry = ttk.Entry(download_section)
        # Custom placeholder behavior
        self.url_entry.insert(0, "Enter Redfin or Zillow URL...")
        self.url_entry.bind('<FocusIn>', lambda e: self.url_entry.delete(0, tk.END) if self.url_entry.get() == "Enter Redfin or Zillow URL..." else None)
        self.url_entry.pack(fill=tk.X, pady=(0, 10), ipady=5)
        
        # Add right-click menu to url_entry
        self.add_right_click_menu(self.url_entry)
        
        # Download buttons in 2-column layout
        button_grid = ttk.Frame(download_section)
        button_grid.pack(fill=tk.X, pady=(0, 0))
        button_grid.columnconfigure(0, weight=1)
        button_grid.columnconfigure(1, weight=1)
        
        self.download_btn = ttk.Button(button_grid, text=" ↓  START", command=self.start_download)
        self.download_btn.grid(row=0, column=0, sticky='ew', padx=(0, 3), ipady=5)
        
        self.stop_btn = ttk.Button(button_grid, text=" ⬛  STOP", command=self.stop_download, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, sticky='ew', padx=(3, 0), ipady=5)
        
        # Progress section (Subtle)
        self.progress_var = tk.StringVar(value="System Ready")
        self.status_label = ttk.Label(download_section, textvariable=self.progress_var, style="Sub.TLabel")
        self.status_label.pack(anchor=tk.W, pady=(10, 0))
        
        self.progress_bar = ttk.Progressbar(download_section, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Explorer section
        explorer_label = ttk.Label(left_frame, text="PROPERTY ADDRESSES", style="Sub.TLabel")
        explorer_label.pack(anchor=tk.W, pady=(10, 5))
        
        explorer_container = ttk.Frame(left_frame)
        explorer_container.pack(fill=tk.BOTH, expand=True)
        
        # Using Treeview for explorer look (Removed visible scrollbars for cleaner look)
        self.explorer_tree = ttk.Treeview(explorer_container, show='tree', selectmode='browse')
        self.explorer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Auto-configure column to stretch
        self.explorer_tree.column("#0", stretch=True, width=300)
        
        self.explorer_tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # Refresh container - 2 column layout
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Configure grid columns to expand equally
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        ttk.Button(button_frame, text=" 🔄  REFRESH", command=self.refresh_properties).grid(row=0, column=0, sticky='ew', padx=(0, 3))
        ttk.Button(button_frame, text=" 🔔  UPDATES", command=self.manual_update_check).grid(row=0, column=1, sticky='ew', padx=(3, 0))
        
        # === RIGHT PANEL - GALLERY VIEWER ===
        
        # Top Gallery Controls
        gallery_header = ttk.Frame(right_frame)
        gallery_header.pack(fill=tk.X, pady=(0, 20))
        
        self.property_label = ttk.Label(gallery_header, text="Ready to browse", style="Header.TLabel")
        self.property_label.pack(side=tk.LEFT)
        
        # Right aligned controls
        controls_frame = ttk.Frame(gallery_header)
        controls_frame.pack(side=tk.RIGHT)
        
        # Exit button
        exit_btn = ttk.Button(controls_frame, text="Exit", style="Exit.TButton", command=self.root.destroy)
        exit_btn.pack(side=tk.LEFT, padx=3)
        
        # Delete and Open Folder buttons
        ttk.Button(gallery_header, text="Delete Property", command=self.delete_property).pack(side=tk.RIGHT, padx=3)
        ttk.Button(gallery_header, text="Open Folder", command=self.open_folder).pack(side=tk.RIGHT, padx=3)
        
        # Property Details Panel
        details_frame = ttk.LabelFrame(right_frame, text=" Property Details ", padding=15)
        details_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Details grid
        details_grid = ttk.Frame(details_frame)
        details_grid.pack(fill=tk.X)
        
        # Price
        price_frame = ttk.Frame(details_grid)
        price_frame.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(price_frame, text="Price:", style="Sub.TLabel").pack(anchor=tk.W)
        self.price_label = ttk.Label(price_frame, text="—", font=("Segoe UI", 12, "bold"), foreground=self.colors['accent'])
        self.price_label.pack(anchor=tk.W)
        
        # Beds/Baths/SqFt
        stats_frame = ttk.Frame(details_grid)
        stats_frame.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(stats_frame, text="Beds | Baths | Sq Ft:", style="Sub.TLabel").pack(anchor=tk.W)
        self.stats_label = ttk.Label(stats_frame, text="—", font=("Segoe UI", 10))
        self.stats_label.pack(anchor=tk.W)
        
        # Description
        desc_container = ttk.Frame(details_frame)
        desc_container.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        ttk.Label(desc_container, text="Description:", style="Sub.TLabel").pack(anchor=tk.W)
        self.description_label = ttk.Label(desc_container, text="No property selected", 
                                          wraplength=800, justify=tk.LEFT, style="TLabel")
        self.description_label.pack(anchor=tk.W, pady=(5, 0))
        
        # URL section
        url_container = ttk.Frame(details_frame)
        url_container.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(url_container, text="Listing URL:", style="Sub.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        self.open_url_btn = ttk.Button(url_container, text="Open in Browser", command=self.open_listing_url, state=tk.DISABLED)
        self.open_url_btn.pack(side=tk.LEFT)
        self.listing_url = None
        
        # Info bar
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.image_counter = ttk.Label(info_frame, text="0 images loaded", style="Sub.TLabel")
        self.image_counter.pack(side=tk.LEFT)
        
        zoom_frame = ttk.Frame(info_frame)
        zoom_frame.pack(side=tk.RIGHT)
        
        ttk.Label(zoom_frame, text="View size:", style="Sub.TLabel").pack(side=tk.LEFT, padx=5)
        self.zoom_slider = ttk.Scale(zoom_frame, from_=150, to=800, orient=tk.HORIZONTAL, 
                                      command=self.on_zoom_change, length=150)
        self.zoom_slider.pack(side=tk.LEFT, padx=5)
        self.zoom_label = ttk.Label(zoom_frame, text="400px", style="Sub.TLabel")
        self.zoom_label.pack(side=tk.LEFT, padx=(5, 0))
        self.zoom_slider.set(400)
        
        # Gallery Area
        gallery_outer = ttk.Frame(right_frame)
        gallery_outer.pack(fill=tk.BOTH, expand=True)
        
        gallery_scrollbar = ttk.Scrollbar(gallery_outer, orient=tk.VERTICAL)
        gallery_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.gallery_canvas = tk.Canvas(
            gallery_outer, 
            bg=self.colors['bg'], 
            yscrollcommand=gallery_scrollbar.set,
            highlightthickness=0,
            borderwidth=0
        )
        self.gallery_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        gallery_scrollbar.config(command=self.gallery_canvas.yview)
        
        self.gallery_container = ttk.Frame(self.gallery_canvas)
        self.gallery_canvas_window = self.gallery_canvas.create_window((0, 0), window=self.gallery_container, anchor=tk.NW)
        
        self.gallery_container.bind('<Configure>', lambda e: self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all")))
        self.gallery_canvas.bind('<Configure>', self.on_gallery_resize)
        self.gallery_canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
        # Bottom Status Bar
        status_bar = tk.Frame(self.root, bg=self.colors['accent'], height=25)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.footer_stats_label = tk.Label(status_bar, text=f"Ready | Version {self.version} | Connected", 
                                    bg=self.colors['accent'], fg="white", font=("Segoe UI", 8, "bold"), padx=10)
        self.footer_stats_label.pack(side=tk.LEFT)
        
        # Add tiny resize grip look-alike
        tk.Label(status_bar, text=" ● Tonys Downloader Engine Active ", bg=self.colors['accent'], fg="white", 
                 font=("Segoe UI", 8), padx=10).pack(side=tk.RIGHT)

    def on_zoom_change(self, value):
        """Handle zoom slider change."""
        if not hasattr(self, 'zoom_label'):
            return
            
        new_size = int(float(value))
        self.thumbnail_size = new_size
        self.zoom_label.config(text=f"{self.thumbnail_size}px")
        
        # Only reload if size changed significantly (every 10px) to reduce re-renders
        if hasattr(self, '_last_size') and abs(new_size - self._last_size) < 10:
            return
        
        self._last_size = new_size
        
        # Reload gallery with new size if images are loaded
        if self.current_images:
            self.display_gallery()
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.gallery_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_gallery_resize(self, event):
        """Handle gallery canvas resize to reflow thumbnails."""
        if self.current_images:
            self.display_gallery()
    
    def get_image_files(self, folder_path):
        """Get all image files (jpg, png, webp) from a folder."""
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            images.extend(glob.glob(os.path.join(folder_path, ext)))
            # Don't check uppercase separately - it causes duplicates on case-insensitive filesystems
        return sorted(list(set(images)))  # Remove any duplicates and sort
    
    def add_right_click_menu(self, widget):
        """Add right-click context menu to a widget."""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: widget.select_range(0, tk.END))

        def show_menu(event):
            widget.focus_set()
            menu.tk_popup(event.x_root, event.y_root)
            return "break"

        widget.bind("<Button-3>", show_menu)

    def refresh_properties(self):
        """Refresh the list of downloaded properties."""
        for item in self.explorer_tree.get_children():
            self.explorer_tree.delete(item)
            
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            return
        
        properties = [d for d in os.listdir(self.output_folder) 
                     if os.path.isdir(os.path.join(self.output_folder, d))]
        
        properties.sort(reverse=True)
        
        for prop in properties:
            prop_path = os.path.join(self.output_folder, prop)
            images = self.get_image_files(prop_path)
            image_count = len(images)
            
            # Insert property node
            item_id = self.explorer_tree.insert('', tk.END, text=f" 🏠 {prop}", values=(prop,))
            # Insert a "Photos" sub-node to look like the mockup explorer
            self.explorer_tree.insert(item_id, tk.END, text=f"   📸 Photos ({image_count})", tags=('subnode',))
    
    def on_tree_select(self, event):
        """Handle property selection from the tree."""
        selection = self.explorer_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        # If user clicks a subnode, get parent's text
        parent = self.explorer_tree.parent(item)
        if parent:
            item = parent
            
        property_name = self.explorer_tree.item(item, "text").split("🏠 ", 1)[-1].strip()
        self.load_property_images(property_name)
    
    def load_property_images(self, property_name):
        """Load all images for a selected property."""
        self.current_property = property_name
        property_path = os.path.join(self.output_folder, property_name)
        
        self.current_images = self.get_image_files(property_path)
        
        if not self.current_images:
            messagebox.showwarning("No Images", f"No images found in {property_name}")
            return
        
        # Load property details
        self.load_property_details(property_path)
        
        # Clear cache when loading new property
        self.thumbnail_cache.clear()
        
        self.property_label.config(text=property_name)
        self.image_counter.config(text=f"{len(self.current_images)} images loaded")
        self.display_gallery()
    
    def load_property_details(self, property_path):
        """Load and display property details from JSON file."""
        import json
        details_file = os.path.join(property_path, 'property_details.json')
        
        if os.path.exists(details_file):
            try:
                with open(details_file, 'r') as f:
                    details = json.load(f)
                
                # Update UI with details
                self.price_label.config(text=details.get('price', 'N/A'))
                
                stats_text = f"{details.get('beds', '—')} | {details.get('baths', '—')} | {details.get('sqft', '—')}"
                self.stats_label.config(text=stats_text)
                
                self.description_label.config(text=details.get('description', 'No description available'))
                
                # Store and enable URL button
                self.listing_url = details.get('url')
                if self.listing_url:
                    self.open_url_btn.config(state=tk.NORMAL)
                else:
                    self.open_url_btn.config(state=tk.DISABLED)
            except Exception as e:
                print(f"Error loading property details: {e}")
                self.reset_property_details()
        else:
            self.reset_property_details()
    
    def reset_property_details(self):
        """Reset property details to default values."""
        self.price_label.config(text="—")
        self.stats_label.config(text="—")
        self.description_label.config(text="No details available for this property")
        self.listing_url = None
        self.open_url_btn.config(state=tk.DISABLED)
    
    def open_listing_url(self):
        """Open the property listing URL in default browser."""
        if self.listing_url:
            import webbrowser
            webbrowser.open(self.listing_url)
    
    def display_gallery(self):
        """Display all images as thumbnails in a scrollable gallery."""
        # Clear existing thumbnails
        for widget in self.gallery_container.winfo_children():
            widget.destroy()
        
        self.gallery_thumbnails = []
        self.photo_references = []
        
        if not self.current_images:
            return
        
        # Show loading message
        loading_label = ttk.Label(self.gallery_container, text="Generating Gallery Preview...", font=("Segoe UI", 11, "italic"))
        loading_label.pack(pady=40)
        self.gallery_container.update()
        
        # Load thumbnails in background thread
        thread = threading.Thread(target=self._load_thumbnails_async)
        thread.daemon = True
        thread.start()
    
    def _load_thumbnails_async(self):
        """Load thumbnails in background thread to prevent freezing."""
        try:
            # Calculate thumbnail size and layout
            canvas_width = self.gallery_canvas.winfo_width()
            if canvas_width <= 1:
                canvas_width = 800
            
            thumb_size = self.thumbnail_size  # Use current thumbnail size
            padding = 10
            columns = max(1, (canvas_width - padding) // (thumb_size + padding))
            
            # Process thumbnails
            thumbnails_data = []
            cache_key_prefix = f"{self.current_property}_{thumb_size}"
            
            for idx, image_path in enumerate(self.current_images):
                try:
                    cache_key = f"{cache_key_prefix}_{idx}"
                    
                    # Check cache first
                    if cache_key in self.thumbnail_cache:
                        thumbnails_data.append((idx, self.thumbnail_cache[cache_key], image_path))
                        continue
                    
                    # Load and create thumbnail with optimizations
                    img = Image.open(image_path)
                    
                    # Use NEAREST for faster resizing during initial load
                    # Switch to LANCZOS only for final display
                    img.thumbnail((thumb_size, thumb_size), Image.Resampling.BILINEAR)
                    
                    # Create a square background
                    thumb = Image.new('RGB', (thumb_size, thumb_size), self.colors['card_bg'])
                    
                    # Paste image centered
                    offset_x = (thumb_size - img.width) // 2
                    offset_y = (thumb_size - img.height) // 2
                    thumb.paste(img, (offset_x, offset_y))
                    
                    # Cache the thumbnail
                    self.thumbnail_cache[cache_key] = thumb
                    thumbnails_data.append((idx, thumb, image_path))
                    
                    # Update UI progressively every 10 images for better perceived performance
                    if (idx + 1) % 10 == 0:
                        self.root.after(0, lambda loaded=idx+1, total=len(self.current_images): 
                                      self._update_loading_progress(loaded, total))
                    
                except Exception as e:
                    print(f"Error loading thumbnail {image_path}: {e}")
            
            # Update UI on main thread
            self.root.after(0, lambda: self._display_thumbnails_ui(thumbnails_data, columns, thumb_size, padding))
            
        except Exception as e:
            print(f"Error in thumbnail loading: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load gallery: {e}"))
    
    def _update_loading_progress(self, loaded, total):
        """Update loading progress message."""
        for widget in self.gallery_container.winfo_children():
            if isinstance(widget, ttk.Label) and "Loading" in widget.cget("text"):
                widget.config(text=f"Loading gallery... {loaded}/{total}")
                break
    
    def _display_thumbnails_ui(self, thumbnails_data, columns, thumb_size, padding):
        """Display loaded thumbnails in the UI (called on main thread)."""
        # Clear loading message
        for widget in self.gallery_container.winfo_children():
            widget.destroy()
        
        # Create thumbnail grid with refined card design
        for idx, thumb, image_path in thumbnails_data:
            row = idx // columns
            col = idx % columns
            
            photo = ImageTk.PhotoImage(thumb)
            self.photo_references.append(photo)
            
            # Create card frame with rounded appearance (simulated with relief)
            card_frame = tk.Frame(self.gallery_container, bg=self.colors['border'], relief='flat')
            card_frame.grid(row=row, column=col, padx=padding, pady=padding, sticky='nw')
            
            # Inner frame for content
            inner_frame = tk.Frame(card_frame, bg=self.colors['card_bg'])
            inner_frame.pack(padx=1, pady=1)
            
            # Image label
            label = tk.Label(inner_frame, image=photo, cursor="hand2", bg=self.colors['card_bg'], borderwidth=0)
            label.pack(padx=4, pady=4)
            
            # Caption with property name - Image number
            caption_text = f"{self.current_property.split(',')[0] if self.current_property else 'Property'} - Image {idx + 1}"
            caption_label = tk.Label(inner_frame, text=caption_text, 
                                    font=("Segoe UI", 8), bg=self.colors['card_bg'], 
                                    fg=self.colors['text_dim'], anchor='w')
            caption_label.pack(fill=tk.X, padx=8, pady=(0, 8))
            
            # Bind click event
            label.bind('<Button-1>', lambda e, path=image_path: self.show_fullsize(path))
            
            # Hover effect
            def on_enter(e, frame=card_frame):
                frame.config(bg=self.colors['accent'])
            def on_leave(e, frame=card_frame):
                frame.config(bg=self.colors['border'])
            
            card_frame.bind('<Enter>', on_enter)
            card_frame.bind('<Leave>', on_leave)
            inner_frame.bind('<Enter>', on_enter)
            inner_frame.bind('<Leave>', on_leave)
            label.bind('<Enter>', on_enter)
            label.bind('<Leave>', on_leave)
            
            self.gallery_thumbnails.append((card_frame, photo))
        
        # Update scroll region
        self.gallery_container.update_idletasks()
        self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all"))
    
    def show_fullsize(self, image_path):
        """Show full-size image in a new window with navigation."""
        # Find current image index
        try:
            current_index = self.current_images.index(image_path)
        except ValueError:
            current_index = 0
        
        fullsize_window = tk.Toplevel(self.root)
        fullsize_window.title(os.path.basename(image_path))
        
        # Set consistent size and center on screen
        window_width = 1200
        window_height = 900
        screen_width = fullsize_window.winfo_screenwidth()
        screen_height = fullsize_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        fullsize_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        fullsize_window.configure(bg=self.colors['bg'])
        
        # Container for navigation and image
        main_container = ttk.Frame(fullsize_window)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Navigation bar at top
        nav_bar = ttk.Frame(main_container)
        nav_bar.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        # Image counter
        counter_label = ttk.Label(nav_bar, text=f"Image {current_index + 1} of {len(self.current_images)}", 
                                 style="Sub.TLabel")
        counter_label.pack(side=tk.LEFT)
        
        # Keyboard shortcut hint
        hint_label = ttk.Label(nav_bar, text="Use ← → arrow keys to navigate", 
                              style="Sub.TLabel", foreground=self.colors['text_dim'])
        hint_label.pack(side=tk.LEFT, padx=20)
        
        # Navigation buttons
        nav_buttons = ttk.Frame(nav_bar)
        nav_buttons.pack(side=tk.RIGHT)
        
        prev_btn = ttk.Button(nav_buttons, text="◀ Previous", width=12)
        prev_btn.pack(side=tk.LEFT, padx=3)
        
        next_btn = ttk.Button(nav_buttons, text="Next ▶", width=12)
        next_btn.pack(side=tk.LEFT, padx=3)
        
        # Create canvas for image
        canvas_frame = ttk.Frame(main_container)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        canvas = tk.Canvas(canvas_frame, bg=self.colors['card_bg'], highlightthickness=0, cursor="hand2")
        canvas.pack(fill=tk.BOTH, expand=True)
        
        def load_image(index):
            """Load and display image at given index."""
            if 0 <= index < len(self.current_images):
                try:
                    img_path = self.current_images[index]
                    img = Image.open(img_path)
                    
                    # Get canvas size
                    canvas.update()
                    win_width = canvas.winfo_width()
                    win_height = canvas.winfo_height()
                    
                    # Scale to fit
                    img_ratio = img.width / img.height
                    win_ratio = win_width / win_height
                    
                    if img_ratio > win_ratio:
                        new_width = win_width - 40
                        new_height = int(new_width / img_ratio)
                    else:
                        new_height = win_height - 40
                        new_width = int(new_height * img_ratio)
                    
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    # Clear and display
                    canvas.delete("all")
                    canvas.create_image(win_width // 2, win_height // 2, image=photo, anchor=tk.CENTER)
                    canvas.image = photo
                    
                    # Update counter and title
                    counter_label.config(text=f"Image {index + 1} of {len(self.current_images)}")
                    fullsize_window.title(os.path.basename(img_path))
                    
                    # Update button states
                    prev_btn.config(state=tk.NORMAL if index > 0 else tk.DISABLED)
                    next_btn.config(state=tk.NORMAL if index < len(self.current_images) - 1 else tk.DISABLED)
                    
                    return index
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load image: {e}")
            return current_index
        
        # Navigation functions
        current_idx = [current_index]  # Use list to allow modification in nested function
        
        def show_previous(event=None):
            if current_idx[0] > 0:
                current_idx[0] = load_image(current_idx[0] - 1)
        
        def show_next(event=None):
            if current_idx[0] < len(self.current_images) - 1:
                current_idx[0] = load_image(current_idx[0] + 1)
        
        # Bind navigation
        prev_btn.config(command=show_previous)
        next_btn.config(command=show_next)
        
        # Keyboard shortcuts
        fullsize_window.bind('<Left>', show_previous)
        fullsize_window.bind('<Right>', show_next)
        fullsize_window.bind('<Escape>', lambda e: fullsize_window.destroy())
        
        # Click to close
        canvas.bind('<Button-1>', lambda e: fullsize_window.destroy())
        
        # Load initial image
        load_image(current_index)
        
        # Set focus to window so keyboard shortcuts work immediately
        fullsize_window.focus_force()
    
    def open_folder(self):
        """Open the current property folder in file explorer."""
        if not self.current_property:
            messagebox.showwarning("No Property", "Please select a property first")
            return
        
        property_path = os.path.join(self.output_folder, self.current_property)
        
        if sys.platform == 'win32':
            os.startfile(property_path)
        elif sys.platform == 'darwin':
            subprocess.run(['open', property_path])
        else:
            subprocess.run(['xdg-open', property_path])
    
    def delete_property(self):
        """Delete the currently selected property folder."""
        if not self.current_property:
            messagebox.showwarning("No Property", "Please select a property first")
            return
        
        property_path = os.path.join(self.output_folder, self.current_property)
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Delete Property",
            f"Are you sure you want to delete:\n\n{self.current_property}\n\nThis will permanently delete all images for this property."
        )
        
        if confirm:
            try:
                import shutil
                shutil.rmtree(property_path)
                messagebox.showinfo("Deleted", f"Property deleted: {self.current_property}")
                
                # Clear current selection and refresh
                self.current_property = None
                self.current_images = []
                self.property_label.config(text="Ready to browse")
                self.image_counter.config(text="0 images loaded")
                
                # Clear gallery
                for widget in self.gallery_container.winfo_children():
                    widget.destroy()
                self.gallery_thumbnails = []
                self.photo_references = []
                
                # Refresh property list
                self.refresh_properties()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete property: {e}")
    
    def start_download(self):
        """Start downloading images in a background thread."""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showwarning("No URL", "Please enter a Redfin or Zillow URL")
            return
        
        if "redfin.com" not in url and "zillow.com" not in url:
            messagebox.showerror("Invalid URL", "Please enter a valid Redfin or Zillow URL")
            return
        
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.download_cancelled = False
        self.progress_bar.start()
        self.progress_var.set("Downloading...")
        
        thread = threading.Thread(target=self.download_images, args=(url,))
        thread.daemon = True
        thread.start()
    
    def stop_download(self):
        """Stop the current download."""
        self.download_cancelled = True
        self.progress_bar.stop()
        self.progress_var.set("Download cancelled")
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
    
    def download_images(self, url):
        """Download images from Redfin or Zillow (runs in background thread)."""
        try:
            # Detect platform
            if "zillow.com" in url:
                self.download_zillow_images(url)
            else:
                self.download_redfin_images(url)
        except Exception as e:
            self.root.after(0, lambda: self.download_error(str(e)))
    
    def download_redfin_images(self, url):
        """Download images from Redfin."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract address
            address = "property"
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text()
                if '|' in title_text:
                    address = title_text.split('|')[0].strip()
            
            if address == "property":
                address_tag = soup.find('h1', class_='full-address')
                if address_tag:
                    address = address_tag.get_text(strip=True)
            
            address = re.sub(r'[<>:"/\\|?*]', '', address)
            address = address.replace(',', '').strip()
            
            property_folder = os.path.join(self.output_folder, address)
            if not os.path.exists(property_folder):
                os.makedirs(property_folder)
            
            # Extract property details
            details = {
                'address': address,
                'url': url,
                'price': 'N/A',
                'beds': 'N/A',
                'baths': 'N/A',
                'sqft': 'N/A',
                'description': 'No description available'
            }
            
            try:
                # Extract price - multiple possible patterns for Redfin
                price_tag = soup.find('div', class_='statsValue') or \
                            soup.find('span', {'data-rf-test-id': 'av-price'}) or \
                            soup.find('div', {'data-rf-test-id': 'abp-price'})
                if price_tag:
                    details['price'] = price_tag.get_text(strip=True)
                
                # Extract beds/baths/sqft from stats - multiple Redfin patterns
                # Pattern 1: stat-block
                stats_divs = soup.find_all('div', class_='stat-block')
                for stat in stats_divs:
                    span = stat.find(['span', 'div'], class_='statsValue')
                    label = stat.find(['span', 'div'], class_='statsLabel')
                    if span and label:
                        value = span.get_text(strip=True)
                        label_text = label.get_text(strip=True).lower()
                        if 'bed' in label_text: details['beds'] = value
                        elif 'bath' in label_text: details['baths'] = value
                        elif 'sq' in label_text: details['sqft'] = value
                
                # Pattern 2: data-rf-test-id
                if details['beds'] == 'N/A':
                    beds_tag = soup.find(['div', 'span'], {'data-rf-test-id': 'abp-beds'}) or \
                               soup.find(['div', 'span'], {'data-rf-test-id': 'av-beds'})
                    if beds_tag: details['beds'] = beds_tag.get_text(strip=True).split()[0]
                
                if details['baths'] == 'N/A':
                    baths_tag = soup.find(['div', 'span'], {'data-rf-test-id': 'abp-baths'}) or \
                                soup.find(['div', 'span'], {'data-rf-test-id': 'av-baths'})
                    if baths_tag: details['baths'] = baths_tag.get_text(strip=True).split()[0]
                
                if details['sqft'] == 'N/A':
                    sqft_tag = soup.find(['div', 'span'], {'data-rf-test-id': 'abp-sqFt'}) or \
                               soup.find(['div', 'span'], {'data-rf-test-id': 'av-sqFt'})
                    if sqft_tag: details['sqft'] = sqft_tag.get_text(strip=True).split()[0]

                # Pattern 3: Generic span search for keywords if still N/A
                if details['beds'] == 'N/A' or details['baths'] == 'N/A':
                    for span in soup.find_all('span'):
                        text = span.get_text().lower()
                        if 'bed' in text and ' ' in text and details['beds'] == 'N/A':
                            val = text.split()[0]
                            if val.isdigit(): details['beds'] = val
                        elif 'bath' in text and ' ' in text and details['baths'] == 'N/A':
                            val = text.split()[0]
                            if val.isdigit(): details['baths'] = val
                        elif 'sq' in text and 'ft' in text and details['sqft'] == 'N/A':
                            val = text.split()[0].replace(',', '')
                            if val.isdigit(): details['sqft'] = val
                
                # Extract description
                desc_tag = soup.find('div', class_='remarks') or \
                           soup.find('div', {'id': 'marketing-remarks'}) or \
                           soup.find('p', class_='property-description')
                if desc_tag:
                    details['description'] = desc_tag.get_text(strip=True)[:500]
            except Exception as e:
                print(f"Error extracting Redfin property details: {e}")
            
            # Save details to JSON file
            import json
            details_file = os.path.join(property_folder, 'property_details.json')
            with open(details_file, 'w') as f:
                json.dump(details, f, indent=2)
            
            # Extract images - try multiple patterns
            images = []
            
            # Pattern 1: Standard CDN pattern with full photo IDs
            photo_pattern = r'ssl\.cdn-redfin\.com/photo/(\d+)/(?:bigphoto|mbphoto|mbphotov3)/(\d+)/([A-Z0-9]+_\d+(?:_[A-Z0-9]+)?)\.'
            matches = re.findall(photo_pattern, response.text)
            
            if matches:
                seen = set()
                for cdn_num, photo_id, photo_name in matches:
                    key = f"{photo_id}/{photo_name}"
                    if key not in seen:
                        seen.add(key)
                        images.append((cdn_num, photo_id, photo_name))
            
            # Pattern 2: Look for image data in JSON/JavaScript
            if not images:
                json_pattern = r'"url":"https://ssl\.cdn-redfin\.com/photo/(\d+)/bigphoto/(\d+)/([^"]+?)\.'
                json_matches = re.findall(json_pattern, response.text)
                if json_matches:
                    seen = set()
                    for cdn_num, photo_id, photo_name in json_matches:
                        key = f"{photo_id}/{photo_name}"
                        if key not in seen:
                            seen.add(key)
                            images.append((cdn_num, photo_id, photo_name))
            
            if not images:
                self.root.after(0, lambda: self.download_error("No images found on this page"))
                return
            
            # Download images using ThreadPool
            downloaded = 0
            total = len(images)
            
            # Use a thread-safe counter or just calculate at the end
            # For progress updates, we'll use as_completed
            
            def download_task(item):
                idx, (cdn_num, photo_id, photo_name) = item
                if self.download_cancelled:
                    return False
                
                # Try different URL formats
                formats = [
                    ('webp', f"https://ssl.cdn-redfin.com/photo/{cdn_num}/bigphoto/{photo_id}/{photo_name}.webp"),
                    ('jpg', f"https://ssl.cdn-redfin.com/photo/{cdn_num}/bigphoto/{photo_id}/{photo_name}.jpg"),
                ]
                
                for ext, img_url in formats:
                    try:
                        filepath = os.path.join(property_folder, f"{idx:03d}_{photo_name}.{ext}")
                        if os.path.exists(filepath):
                            return True
                        
                        img_response = requests.get(img_url, headers=headers, timeout=10)
                        if img_response.status_code == 200 and len(img_response.content) > 1000:
                            with open(filepath, 'wb') as f:
                                f.write(img_response.content)
                            return True
                    except:
                        continue
                return False

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(download_task, item): item for item in enumerate(images, 1)}
                completed = 0
                
                from concurrent.futures import as_completed
                for future in as_completed(futures):
                    if self.download_cancelled:
                        # Cancel remaining futures
                        for f in futures:
                            f.cancel()
                        break
                    
                    if future.result():
                        downloaded += 1
                    completed += 1
                    self.root.after(0, lambda c=completed, t=total: self.progress_var.set(f"Downloading {c}/{t}..."))

            if self.download_cancelled:
                self.root.after(0, lambda: self.progress_var.set(f"Cancelled - Downloaded {downloaded}/{total}"))
                return
                
            self.root.after(0, lambda: self.download_complete(address, downloaded))
            
        except Exception as e:
            self.root.after(0, lambda: self.download_error(str(e)))
    
    def download_zillow_images(self, url):
        """Download images from Zillow."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract address from Zillow
            address = "property"
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text()
                if '|' in title_text:
                    address = title_text.split('|')[0].strip()
            
            address = re.sub(r'[<>:"/\\|?*]', '', address)
            address = address.replace(',', '').strip()
            
            property_folder = os.path.join(self.output_folder, address)
            if not os.path.exists(property_folder):
                os.makedirs(property_folder)
            
            # Extract Zillow property details
            details = {
                'address': address,
                'url': url,
                'price': 'N/A',
                'beds': 'N/A',
                'baths': 'N/A',
                'sqft': 'N/A',
                'description': 'No description available'
            }
            
            try:
                # Attempt to find Zillow's JSON data in script tags (much more reliable)
                import json
                script_tag = soup.find('script', id='__NEXT_DATA__')
                if script_tag:
                    data = json.loads(script_tag.string)
                    try:
                        # Navigate the complex Zillow JSON structure
                        # CRITICAL: gdpClientCache is often a STRING of JSON, not a dict
                        gdp_raw = data.get('props', {}).get('pageProps', {}).get('componentProps', {}).get('gdpClientCache', '{}')
                        
                        gdp_data = {}
                        if isinstance(gdp_raw, str):
                            gdp_data = json.loads(gdp_raw)
                        else:
                            gdp_data = gdp_raw
                        
                        # Find the key that contains property data (e.g., "ForSalePriorityQuery...")
                        cache_key = next((k for k in gdp_data.keys() if 'PriorityQuery' in k), None)
                        
                        if cache_key:
                            prop = gdp_data[cache_key].get('property', {})
                            
                            if details['price'] == 'N/A' and prop.get('price'):
                                details['price'] = f"${prop.get('price', 0):,}"
                            if details['beds'] == 'N/A' and prop.get('bedrooms'):
                                details['beds'] = str(prop.get('bedrooms'))
                            if details['baths'] == 'N/A' and prop.get('bathrooms'):
                                details['baths'] = str(prop.get('bathrooms'))
                            if details['sqft'] == 'N/A' and prop.get('livingArea'):
                                details['sqft'] = f"{prop.get('livingArea', 0):,}"
                            if details['description'] == 'No description available' and prop.get('description'):
                                details['description'] = prop.get('description')
                    except Exception as e:
                        print(f"Zillow JSON parsing error: {e}")

                # Fallback to HTML parsing if JSON failed or missed something
                if details['price'] == 'N/A':
                    price_tag = soup.find(['span', 'div'], {'data-testid': 'price'})
                    if price_tag: details['price'] = price_tag.get_text(strip=True)
                
                # Improved HTML stats fallback (Zillow uses same test-id for all 3 stats)
                if details['beds'] == 'N/A' or details['baths'] == 'N/A' or details['sqft'] == 'N/A':
                    stat_containers = soup.find_all(['div', 'span'], {'data-testid': 'bed-bath-sqft-fact-container'})
                    for container in stat_containers:
                        text = container.get_text(separator=' ').lower()
                        # Extract the first number found in this specific container
                        num_match = re.search(r'([\d,]+)', text)
                        if num_match:
                            val = num_match.group(1)
                            if 'bed' in text and details['beds'] == 'N/A': details['beds'] = val
                            elif 'bath' in text and details['baths'] == 'N/A': details['baths'] = val
                            elif 'sq' in text and details['sqft'] == 'N/A': details['sqft'] = val

                # Final fallback for stats string like "3 bd 2 ba 1,752 sqft"
                if details['beds'] == 'N/A' or details['sqft'] == 'N/A':
                    stats_container = soup.find('div', {'data-testid': 'bed-bath-sqft-facts'}) or \
                                      soup.find('p', class_='ds-bed-bath-living-area')
                    if stats_container:
                        stats_text = stats_container.get_text(separator=' ').lower()
                        beds_match = re.search(r'(\d+)\s*(?:bd|bed)', stats_text)
                        baths_match = re.search(r'(\d+)\s*(?:ba|bath)', stats_text)
                        sqft_match = re.search(r'([\d,]+)\s*sqft', stats_text)
                        if beds_match and details['beds'] == 'N/A': details['beds'] = beds_match.group(1)
                        if baths_match and details['baths'] == 'N/A': details['baths'] = baths_match.group(1)
                        if sqft_match and details['sqft'] == 'N/A': details['sqft'] = sqft_match.group(1)

                if details['description'] == 'No description available':
                    desc_tag = soup.find('p', {'data-testid': 'main-content'}) or \
                               soup.find('div', {'data-testid': 'description'})
                    if desc_tag: details['description'] = desc_tag.get_text(strip=True)

            except Exception as e:
                print(f"Error extracting Zillow property details: {e}")
                
            # Save details to JSON file
            import json
            details_file = os.path.join(property_folder, 'property_details.json')
            with open(details_file, 'w') as f:
                json.dump(details, f, indent=2)
            
            # Extract Zillow images
            images = []
            zillow_pattern = r'https://photos\.zillowstatic\.com/fp/([a-f0-9]+)-(?:cc_ft_\d+|uncropped_scaled_within_\d+_\d+)'
            matches = re.findall(zillow_pattern, response.text)
            
            if matches:
                seen = set()
                for photo_id in matches:
                    if photo_id not in seen:
                        seen.add(photo_id)
                        images.append(photo_id)
            
            if not images:
                json_pattern = r'"hiResImageLink":"(https://photos\.zillowstatic\.com/fp/[^"]+)"'
                json_matches = re.findall(json_pattern, response.text)
                if json_matches:
                    seen = set()
                    for img_url in json_matches:
                        photo_id_match = re.search(r'/fp/([a-f0-9]+)-', img_url)
                        if photo_id_match:
                            photo_id = photo_id_match.group(1)
                            if photo_id not in seen:
                                seen.add(photo_id)
                                images.append(photo_id)
            
            if not images:
                self.root.after(0, lambda: self.download_error("No images found on this Zillow page"))
                return
            
            # Download images using ThreadPool
            downloaded = 0
            total = len(images)
            
            def download_zillow_task(item):
                idx, photo_id = item
                if self.download_cancelled:
                    return False
                
                size_options = ['cc_ft_1536', 'cc_ft_1344', 'cc_ft_960', 'uncropped_scaled_within_1536_1024']
                
                for size in size_options:
                    try:
                        img_url = f"https://photos.zillowstatic.com/fp/{photo_id}-{size}.webp"
                        filepath = os.path.join(property_folder, f"{idx:03d}_{photo_id}.webp")
                        
                        if os.path.exists(filepath):
                            return True
                        
                        img_response = requests.get(img_url, headers=headers, timeout=10)
                        if img_response.status_code == 200 and len(img_response.content) > 1000:
                            with open(filepath, 'wb') as f:
                                f.write(img_response.content)
                            return True
                        else:
                            # Try JPG fallback
                            img_url_jpg = img_url.replace('.webp', '.jpg')
                            img_response = requests.get(img_url_jpg, headers=headers, timeout=10)
                            if img_response.status_code == 200 and len(img_response.content) > 1000:
                                filepath = filepath.replace('.webp', '.jpg')
                                with open(filepath, 'wb') as f:
                                    f.write(img_response.content)
                                return True
                    except:
                        continue
                return False

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(download_zillow_task, item): item for item in enumerate(images, 1)}
                completed = 0
                
                from concurrent.futures import as_completed
                for future in as_completed(futures):
                    if self.download_cancelled:
                        # Cancel remaining futures
                        for f in futures:
                            f.cancel()
                        break
                    
                    if future.result():
                        downloaded += 1
                    completed += 1
                    self.root.after(0, lambda c=completed, t=total: self.progress_var.set(f"Downloading {c}/{t}..."))

            if self.download_cancelled:
                self.root.after(0, lambda: self.progress_var.set(f"Cancelled - Downloaded {downloaded}/{total}"))
                return
                
            self.root.after(0, lambda: self.download_complete(address, downloaded))
            
        except Exception as e:
            self.root.after(0, lambda: self.download_error(str(e)))
    
    def check_for_updates(self):
        """Check for updates from GitHub releases."""
        def check_update_thread():
            try:
                # GitHub API endpoint for latest release
                api_url = "https://api.github.com/repos/BigTonyTones/Tonys-Redfin-Zillow-Image-Downloader/releases/latest"
                response = requests.get(api_url, timeout=5)
                
                if response.status_code == 200:
                    release_data = response.json()
                    latest_version = release_data.get('tag_name', '').replace('v', '')
                    
                    if latest_version and latest_version > self.version:
                        # New version available
                        self.root.after(0, lambda: self.prompt_update(latest_version, release_data))
            except Exception as e:
                # Silently fail - don't bother user with update check errors
                print(f"Update check failed: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=check_update_thread)
        thread.daemon = True
        thread.start()
    
    def prompt_update(self, new_version, release_data):
        """Prompt user to update to new version."""
        release_notes = release_data.get('body', 'No release notes available.')
        
        message = f"A new version ({new_version}) is available!\n\n"
        message += f"Release Notes:\n{release_notes[:300]}...\n\n"
        message += "Would you like to auto-update now?\n(The app will restart after updating)"
        
        if messagebox.askyesno("Update Available", message):
            self.apply_update(release_data)
    
    def apply_update(self, release_data):
        """Download and apply the update."""
        def update_thread():
            try:
                self.root.after(0, lambda: self.progress_var.set("Downloading update..."))
                
                # Try to find a zip asset, otherwise use the source code zip
                assets = release_data.get('assets', [])
                download_url = None
                
                for asset in assets:
                    if asset.get('name', '').endswith('.zip'):
                        download_url = asset.get('browser_download_url')
                        break
                
                if not download_url:
                    download_url = release_data.get('zipball_url')
                
                if not download_url:
                    self.root.after(0, lambda: messagebox.showerror("Update Error", "Could not find download link."))
                    return
                
                # Download update
                response = requests.get(download_url, stream=True)
                response.raise_for_status()
                
                update_zip = "update_temp.zip"
                with open(update_zip, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.root.after(0, lambda: self.progress_var.set("Extracting update..."))
                
                # Extract zip
                import zipfile
                import shutil
                
                extract_path = "update_extracted"
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)
                
                with zipfile.ZipFile(update_zip, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                
                # Move files from extracted folder (GitHub zip usually has a subfolder)
                subfolders = [f for f in os.listdir(extract_path) if os.path.isdir(os.path.join(extract_path, f))]
                if subfolders:
                    src_dir = os.path.join(extract_path, subfolders[0])
                    for item in os.listdir(src_dir):
                        s = os.path.join(src_dir, item)
                        d = os.path.join(".", item)
                        if os.path.isdir(s):
                            if os.path.exists(d):
                                shutil.rmtree(d)
                            shutil.copytree(s, d)
                        else:
                            shutil.copy2(s, d)
                
                # Ensure startup.sh is executable on Linux/Mac
                if sys.platform != 'win32':
                    try:
                        startup_script = os.path.abspath("startup.sh")
                        if os.path.exists(startup_script):
                            os.chmod(startup_script, 0o755)
                    except Exception as e:
                        print(f"Failed to set permissions on startup.sh: {e}")

                # Cleanup
                if os.path.exists(update_zip):
                    os.remove(update_zip)
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)
                
                self.root.after(0, lambda: messagebox.showinfo("Update Complete", "Application updated successfully! The app will now restart."))
                
                # Restart
                self.root.after(0, self.restart_app)
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Update Error", f"Failed to apply update: {e}"))
                self.root.after(0, lambda: self.progress_var.set("System Ready"))
        
        thread = threading.Thread(target=update_thread)
        thread.daemon = True
        thread.start()

    def restart_app(self):
        """Restart the current application."""
        import sys
        import os
        
        python = sys.executable
        if sys.platform == 'win32':
            # On Windows, start a new process and exit
            os.startfile("Start.bat")
        else:
            # On Linux/Mac, use execv
            os.execv(python, [python] + sys.argv)
        
        self.root.destroy()
        sys.exit()
    
    def manual_update_check(self):
        """Manually check for updates (triggered by button)."""
        def check_update_thread():
            try:
                self.root.after(0, lambda: self.progress_var.set("Checking for updates..."))
                
                api_url = "https://api.github.com/repos/BigTonyTones/Tonys-Redfin-Zillow-Image-Downloader/releases/latest"
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    release_data = response.json()
                    latest_version = release_data.get('tag_name', '').replace('v', '')
                    
                    if latest_version and latest_version > self.version:
                        self.root.after(0, lambda: self.prompt_update(latest_version, release_data))
                    else:
                        self.root.after(0, lambda: messagebox.showinfo("No Updates", f"You're running the latest version ({self.version})!"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Update Check Failed", "Could not connect to update server."))
                
                self.root.after(0, lambda: self.progress_var.set("System Ready"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Update Check Failed", f"Error: {str(e)}"))
                self.root.after(0, lambda: self.progress_var.set("System Ready"))
        
        thread = threading.Thread(target=check_update_thread)
        thread.daemon = True
        thread.start()
    
    def download_complete(self, address, count):
        """Handle successful download completion."""
        self.progress_bar.stop()
        self.progress_var.set("Ready")
        self.download_btn.config(state=tk.NORMAL)
        
        messagebox.showinfo("Success", f"Downloaded {count} images!\n\nSaved to: {address}")
        
        self.refresh_properties()
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, "Enter Redfin or Zillow URL...")
        
        # Update stats
        if hasattr(self, 'footer_stats_label'):
            self.footer_stats_label.config(text=f"Last Download: {count} images | Version {self.version}")
    
    def download_error(self, error_msg):
        """Handle download error."""
        self.progress_bar.stop()
        self.progress_var.set("Error occurred")
        self.download_btn.config(state=tk.NORMAL)
        
        messagebox.showerror("Download Error", f"Failed to download images:\n{error_msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RedfinDownloaderGUI(root)
    root.mainloop()