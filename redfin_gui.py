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
from PIL import Image, ImageTk
import glob

class RedfinDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.version = "1.2"
        
        # Performance & DPI Optimizations for Windows
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
            
        # Optimize Tcl performance
        self.root.tk.call('tk', 'scaling', 1.33) # Match standard 96dpi scaling
        
        self.root.title(f"Tonys Redfin Image Downloader v{self.version}")
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
        
        self.output_folder = "redfin_images"
        self.current_property = None
        self.current_images = []
        self.gallery_thumbnails = []
        self.photo_references = []
        self.thumbnail_size = 400
        self.thumbnail_cache = {}
        
        self.setup_styles()
        self.setup_ui()
        self.refresh_properties()
        
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
        logo_label = ttk.Label(left_frame, text="TONYS DOWNLOADER", font=("Segoe UI Black", 14), foreground=self.colors['fg'])
        logo_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Download section
        download_section = ttk.Frame(left_frame)
        download_section.pack(fill=tk.X, pady=(0, 25))
        
        self.url_entry = ttk.Entry(download_section)
        # Custom placeholder behavior
        self.url_entry.insert(0, "Enter Redfin URL...")
        self.url_entry.bind('<FocusIn>', lambda e: self.url_entry.delete(0, tk.END) if self.url_entry.get() == "Enter Redfin URL..." else None)
        self.url_entry.pack(fill=tk.X, pady=(0, 10), ipady=5)
        
        self.download_btn = ttk.Button(download_section, text=" ↓  START DOWNLOAD", command=self.start_download)
        self.download_btn.pack(fill=tk.X, ipady=5)
        
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
        
        v_scrollbar = ttk.Scrollbar(explorer_container)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(explorer_container, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Using Treeview for explorer look
        self.explorer_tree = ttk.Treeview(explorer_container, show='tree', selectmode='browse', 
                                          yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.explorer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=self.explorer_tree.yview)
        h_scrollbar.config(command=self.explorer_tree.xview)
        
        # Auto-configure column to stretch
        self.explorer_tree.column("#0", stretch=True, width=300)
        
        self.explorer_tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # Refresh container
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(button_frame, text=" 🔄  REFRESH LIBRARY", command=self.refresh_properties).pack(fill=tk.X)
        
        # === RIGHT PANEL - GALLERY VIEWER ===
        
        # Top Gallery Controls
        gallery_header = ttk.Frame(right_frame)
        gallery_header.pack(fill=tk.X, pady=(0, 20))
        
        self.property_label = ttk.Label(gallery_header, text="Ready to browse", style="Header.TLabel")
        self.property_label.pack(side=tk.LEFT)
        
        # Right aligned controls
        controls_frame = ttk.Frame(gallery_header)
        controls_frame.pack(side=tk.RIGHT)
        
        # Mock buttons matching screenshot layout
        for txt in ["Sort by: Date", "Filter: All", "View: Grid"]:
            btn = ttk.Button(controls_frame, text=txt, style="TButton")
            btn.pack(side=tk.LEFT, padx=3)
            
        # Exit button placed to the right of View Grid
        exit_btn = ttk.Button(controls_frame, text="Exit", style="Exit.TButton", command=self.root.destroy)
        exit_btn.pack(side=tk.LEFT, padx=3)
            
        ttk.Button(gallery_header, text=" 📂  EXPLORER", command=self.open_folder).pack(side=tk.RIGHT, padx=10)
        
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
        
        self.stats_label = tk.Label(status_bar, text=f"Ready | Version {self.version} | Connected", 
                                    bg=self.colors['accent'], fg="white", font=("Segoe UI", 8, "bold"), padx=10)
        self.stats_label.pack(side=tk.LEFT)
        
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
        
        # Clear cache when loading new property
        self.thumbnail_cache.clear()
        
        self.property_label.config(text=property_name)
        self.image_counter.config(text=f"{len(self.current_images)} images")
        self.display_gallery()
    
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
        """Show full-size image in a new window."""
        fullsize_window = tk.Toplevel(self.root)
        fullsize_window.title(os.path.basename(image_path))
        fullsize_window.geometry("1200x900")
        fullsize_window.configure(bg=self.colors['bg'])
        
        # Create canvas for image
        canvas_frame = ttk.Frame(fullsize_window)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        canvas = tk.Canvas(canvas_frame, bg=self.colors['card_bg'], highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        try:
            # Load image
            img = Image.open(image_path)
            
            # Get window size
            fullsize_window.update()
            win_width = fullsize_window.winfo_width()
            win_height = fullsize_window.winfo_height()
            
            # Scale to fit window
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
            
            # Display image
            canvas.create_image(win_width // 2, win_height // 2, image=photo, anchor=tk.CENTER)
            canvas.image = photo
            
            # Add close button
            close_btn = ttk.Button(fullsize_window, text="Close", command=fullsize_window.destroy)
            close_btn.pack(pady=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            fullsize_window.destroy()
    
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
    
    def start_download(self):
        """Start downloading images in a background thread."""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showwarning("No URL", "Please enter a Redfin URL")
            return
        
        if "redfin.com" not in url:
            messagebox.showerror("Invalid URL", "Please enter a valid Redfin URL")
            return
        
        self.download_btn.config(state=tk.DISABLED)
        self.progress_bar.start()
        self.progress_var.set("Downloading...")
        
        thread = threading.Thread(target=self.download_images, args=(url,))
        thread.daemon = True
        thread.start()
    
    def download_images(self, url):
        """Download images from Redfin (runs in background thread)."""
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
            
            # Download images
            downloaded = 0
            total = len(images)
            
            for idx, (cdn_num, photo_id, photo_name) in enumerate(images, 1):
                self.root.after(0, lambda i=idx, t=total: self.progress_var.set(f"Downloading {i}/{t}..."))
                
                # Try different URL formats using the CDN number from the page
                formats = [
                    ('webp', f"https://ssl.cdn-redfin.com/photo/{cdn_num}/bigphoto/{photo_id}/{photo_name}.webp"),
                    ('jpg', f"https://ssl.cdn-redfin.com/photo/{cdn_num}/bigphoto/{photo_id}/{photo_name}.jpg"),
                ]
                
                success = False
                for ext, img_url in formats:
                    try:
                        filepath = os.path.join(property_folder, f"{idx:03d}_{photo_name}.{ext}")
                        
                        if os.path.exists(filepath):
                            downloaded += 1
                            success = True
                            break
                        
                        img_response = requests.get(img_url, headers=headers, timeout=10)
                        if img_response.status_code == 200 and len(img_response.content) > 1000:
                            with open(filepath, 'wb') as f:
                                f.write(img_response.content)
                            downloaded += 1
                            success = True
                            print(f"Downloaded: {img_url}")
                            break
                        else:
                            print(f"Failed {img_response.status_code}: {img_url}")
                    except Exception as e:
                        print(f"Error downloading {img_url}: {e}")
                        continue
                
                if not success:
                    print(f"Could not download image {idx}: {photo_id}/{photo_name}")
                
                time.sleep(0.2)
            
            self.root.after(0, lambda: self.download_complete(address, downloaded))
            
        except Exception as e:
            self.root.after(0, lambda: self.download_error(str(e)))
    
    def download_complete(self, address, count):
        """Handle successful download completion."""
        self.progress_bar.stop()
        self.progress_var.set("Ready")
        self.download_btn.config(state=tk.NORMAL)
        
        messagebox.showinfo("Success", f"Downloaded {count} images!\n\nSaved to: {address}")
        
        self.refresh_properties()
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, "Enter Redfin URL...")
        
        # Update stats
        if hasattr(self, 'stats_label'):
            self.stats_label.config(text=f"Last Download: {count} images | Version {self.version}")
    
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