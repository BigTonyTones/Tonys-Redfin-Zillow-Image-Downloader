# Tonys Redfin Zillow Image Downloader v1.9.8

A high-performance tool designed to capture high-res photos from Redfin and Zillow listings instantly. Featuring a sleek dark theme, multi-threaded downloading, and automatic property metadata extraction.

![App Preview](assets/dashboard_v1_9_3.png)

### Key Features:
- **Lightning Fast**: Multi-threaded engine downloads up to 10 images simultaneously.
- **Smart Metadata**: Automatically scrapes Price, Beds, Baths, Sq Ft, and Descriptions.
- **Auto-Updates**: One-click updates and restarts directly from GitHub releases.
- **Built-in Gallery**: Browse your downloads and manage property folders within the app.
- **Dynamic View**: Adjustable thumbnail sizes and high-DPI support for crisp viewing.

### How to use it:

**Windows:**
1.  **Clone the repo**: 
    ```bash
    git clone https://github.com/BigTonyTones/Tonys-Redfin-Zillow-Image-Downloader.git
    cd Tonys-Redfin-Zillow-Image-Downloader
    ```
2.  **Run**: Double-click `Start.bat`
3.  **Paste**: Put a Redfin or Zillow link in the box and hit Download.
4.  **Browse**: Click a property in your library on the left to see the photos.

**macOS (Double-Click Launcher):**
1.  **Clone or Download the repo**:
    ```bash
    git clone https://github.com/BigTonyTones/Tonys-Redfin-Zillow-Image-Downloader.git
    cd Tonys-Redfin-Zillow-Image-Downloader
    ```
2.  **Run**: Double-click `Start_on_Mac.command` to launch the app!
    *Note: If macOS displays a permission warning on double-click (which can happen if downloaded as a ZIP), just open Terminal once, type `chmod +x ` (with a space at the end), drag and drop the `Start_on_Mac.command` file onto the Terminal window, and press **Enter**. You only need to do this once!*
    *🎨 **Custom Icon**: To set a custom icon for the script, open `assets/app_icon.png` in Preview and press **Cmd + C** (Copy). Right-click `Start_on_Mac.command` in Finder, click **Get Info**, click the tiny file icon in the top-left corner of the window, and press **Cmd + V** (Paste).*
3.  **Setup & Launch**: The launcher will verify Python 3 and Tkinter are installed, and automatically guide you through getting them if needed.

**Linux:**
1.  **Clone the repo**:
    ```bash
    git clone https://github.com/BigTonyTones/Tonys-Redfin-Zillow-Image-Downloader.git
    cd Tonys-Redfin-Zillow-Image-Downloader
    ```
2.  **Make executable**: `chmod +x startup.sh`
3.  **Run**: `./startup.sh`

### Requirements:
Requires Python 3. The app will help you install the other stuff (`requests`, `beautifulsoup4`, `Pillow`) if you don't have them yet.

---
*Created by Tony*
