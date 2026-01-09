# Tonys Redfin Zillow Image Downloader v1.5

I made this tool to quickly grab high-res photos from Redfin and Zillow listings. It has a nice dark theme, it's fast, and it automatically organizes everything into folders by address so you don't have to.

![App Preview](assets/screenshot.png)

### What it does:
- **Grabs High-Res Photos**: Pulls the best quality images directly from Redfin and Zillow.
- **Built-in Gallery**: You can browse your downloads right inside the app.
- **Adjustable View**: Use the slider to make thumbnails bigger or smaller.
- **Safe Setup**: It'll ask you before installing any missing Python packages.
- **Folders**: Every property gets its own folder named after the address.

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

**Linux/Mac:**
1.  **Clone the repo**: 
    ```bash
    git clone https://github.com/BigTonyTones/Tonys-Redfin-Zillow-Image-Downloader.git
    cd Tonys-Redfin-Zillow-Image-Downloader
    ```
2.  **Make executable**: `chmod +x startup.sh`
3.  **Run**: `./startup.sh`
4.  **Paste**: Put a Redfin or Zillow link in the box and hit Download.
5.  **Browse**: Click a property in your library on the left to see the photos.

### Requirements:
Requires Python 3. The app will help you install the other stuff (`requests`, `beautifulsoup4`, `Pillow`) if you don't have them yet.

---
*Created by Tony*
