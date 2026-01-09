import subprocess
import sys

# Check and potentially install dependencies
def check_dependencies():
    """Check for required packages and ask user for permission to install missing ones."""
    required_packages = ['requests', 'beautifulsoup4']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package if package != 'beautifulsoup4' else 'bs4')
        except ImportError:
            missing.append(package)
            
    if missing:
        print(f"\nThe following dependencies are missing: {', '.join(missing)}")
        choice = input("Would you like to install them now? (y/n): ").lower()
        if choice == 'y':
            for package in missing:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print("Dependencies installed successfully!\n")
        else:
            print("Warning: Missing dependencies may cause the script to fail.\n")

# Check dependencies first
check_dependencies()

import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin, urlparse
import time

def download_redfin_images(url, output_folder="redfin_images"):
    """
    Download all images from a Redfin property listing.
    
    Args:
        url: The Redfin property URL
        output_folder: Folder to save images (default: 'redfin_images')
    """
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    print(f"Fetching page: {url}")
    
    # Set headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Fetch the page
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract address from the page
        address = "property"  # default fallback
        
        # Try to find the address in the page title or meta tags
        title_tag = soup.find('title')
        if title_tag:
            # Title format: "25221 Summerhill Ln, Stevenson Ranch, CA 91381 | MLS# SR25185749 | Redfin"
            title_text = title_tag.get_text()
            # Extract just the address part (before the first |)
            if '|' in title_text:
                address = title_text.split('|')[0].strip()
        
        # Fallback: try h1 with class 'full-address'
        if address == "property":
            address_tag = soup.find('h1', class_='full-address')
            if address_tag:
                address = address_tag.get_text(strip=True)
        
        # Clean up address for use as folder name (remove invalid characters)
        address = re.sub(r'[<>:"/\\|?*]', '', address)  # Remove invalid filename chars
        address = address.replace(',', '').strip()  # Remove commas
        
        # Create property folder with address as name
        property_folder = os.path.join(output_folder, address)
        
        if not os.path.exists(property_folder):
            os.makedirs(property_folder)
        
        print(f"Saving to folder: {address}")
        
        # Find all image URLs in the page source
        # Look for patterns like: /photo/45/bigphoto/749/SR25185749_1.webp
        images = []
        
        # Extract all photo URLs from the HTML
        photo_pattern = r'ssl\.cdn-redfin\.com/photo/\d+/(?:bigphoto|mbphoto|mbphotov3)/(\d+)/([A-Z0-9]+_\d+(?:_\d+)?)\.(webp|jpg)'
        matches = re.findall(photo_pattern, response.text)
        
        if matches:
            photo_id = matches[0][0]
            # Get unique photo identifiers
            seen = set()
            for photo_id, photo_name, ext in matches:
                if photo_name not in seen:
                    seen.add(photo_name)
                    images.append((photo_id, photo_name))
            
            print(f"Found {len(images)} unique images")
        
        # If no images found, try a broader search
        if not images:
            print("No photo patterns found, trying broader search...")
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src and 'ssl.cdn-redfin.com/photo' in src and 'bigphoto' in src:
                    images.append(src)
        
        print(f"Found {len(images)} images")
        
        # Download each image
        downloaded = 0
        failed_urls = []
        
        for idx, img_data in enumerate(images, 1):
            try:
                # Handle tuple format (photo_id, photo_name)
                if isinstance(img_data, tuple):
                    photo_id, photo_name = img_data
                    
                    # Try webp first (better quality), fall back to jpg
                    formats = [
                        ('webp', f"https://ssl.cdn-redfin.com/photo/45/bigphoto/{photo_id}/{photo_name}.webp"),
                        ('jpg', f"https://ssl.cdn-redfin.com/photo/45/bigphoto/{photo_id}/{photo_name}.jpg")
                    ]
                    
                    full_url = None
                    filename = None
                    
                    for ext, url in formats:
                        try:
                            img_response = requests.get(url, headers=headers, timeout=10)
                            if img_response.status_code == 200:
                                full_url = url
                                filename = f"{photo_name}.{ext}"
                                break
                        except:
                            continue
                    
                    if not full_url:
                        print(f"Skipped {idx}: Could not download {photo_name}")
                        continue
                        
                else:
                    # Handle URL string format (fallback)
                    full_url = urljoin(url, img_data)
                    parsed = urlparse(full_url)
                    filename = os.path.basename(parsed.path)
                    
                    # Download
                    img_response = requests.get(full_url, headers=headers, timeout=10)
                    if img_response.status_code != 200:
                        continue
                
                if not filename:
                    filename = f"image_{idx}.jpg"
                
                filepath = os.path.join(property_folder, f"{idx:03d}_{filename}")
                
                # Skip if already downloaded
                if os.path.exists(filepath):
                    print(f"Skipped (already exists): {filename}")
                    downloaded += 1
                    continue
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(img_response.content)
                
                downloaded += 1
                print(f"Downloaded {downloaded}/{len(images)}: {filename}")
                
                # Be polite - small delay between downloads
                time.sleep(0.2)
                
            except Exception as e:
                failed_urls.append(str(img_data))
                print(f"Failed: {img_data} - {e}")
        
        if failed_urls:
            print(f"\nFailed to download {len(failed_urls)} images")
        
        print(f"\nCompleted! Successfully downloaded {downloaded} images to {property_folder}")
        return property_folder
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("Tonys Redfin Image Downloader v1.2")
    print("=" * 50)
    print()
    
    # Ask for URL at the beginning
    url = input("Enter Redfin listing URL: ").strip()
    
    if not url:
        print("Error: No URL provided!")
        sys.exit(1)
    
    if "redfin.com" not in url:
        print("Error: Please provide a valid Redfin URL")
        sys.exit(1)
    
    print()
    download_redfin_images(url)