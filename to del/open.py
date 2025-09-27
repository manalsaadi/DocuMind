import webbrowser
import time
import os
import subprocess
import platform

def open_multiple_pages_firefox(urls, delay=1):
    """
    Opens multiple webpages in Firefox browser.
    
    Args:
        urls (list): List of URLs to open
        delay (float): Delay between opening each page (in seconds)
    """
    
    # Try to find Firefox executable on Windows
    firefox_paths = [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        os.path.expanduser(r"~\AppData\Local\Mozilla Firefox\firefox.exe")
    ]
    
    firefox_path = None
    for path in firefox_paths:
        if os.path.exists(path):
            firefox_path = path
            break
    
    if firefox_path:
        # Register Firefox as the browser
        webbrowser.register('firefox', None, webbrowser.BackgroundBrowser(firefox_path))
        browser = webbrowser.get('firefox')
        
        print(f"Opening {len(urls)} webpages in Firefox...")
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"Opening page {i}: {url}")
                browser.open_new_tab(url)
                
                # Add delay between opening pages to prevent overwhelming the browser
                if i < len(urls):  # Don't delay after the last URL
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"Error opening {url}: {e}")
    else:
        print("Firefox not found. Trying with default browser...")
        # Fallback to default browser
        for i, url in enumerate(urls, 1):
            try:
                print(f"Opening page {i}: {url}")
                webbrowser.open_new_tab(url)
                
                if i < len(urls):
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"Error opening {url}: {e}")

def open_firefox_with_multiple_tabs(urls):
    """
    Alternative method: Opens Firefox with multiple tabs at once using command line.
    This method opens all URLs in a single Firefox window with multiple tabs.
    """
    firefox_paths = [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        os.path.expanduser(r"~\AppData\Local\Mozilla Firefox\firefox.exe")
    ]
    
    firefox_path = None
    for path in firefox_paths:
        if os.path.exists(path):
            firefox_path = path
            break
    
    if firefox_path:
        try:
            # Create command to open all URLs at once
            cmd = [firefox_path] + urls
            subprocess.Popen(cmd)
            print(f"Opened {len(urls)} tabs in Firefox")
        except Exception as e:
            print(f"Error opening Firefox with multiple tabs: {e}")
    else:
        print("Firefox not found. Please install Firefox or check the installation path.")

def convert_urls(text):
    """Simple function to convert text URLs to Python list format"""
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    formatted = ['        "' + line + '"' for line in lines]
    return '[\n' + ',\n'.join(formatted) + '\n]'

if __name__ == "__main__":
    # Example URLs - modify this list with your desired webpages
    urls_to_open = [
        "https://www.google.com",
        "https://www.github.com",
        "https://www.stackoverflow.com",
        "https://www.python.org",
        "https://www.mozilla.org"
    ]

    
    
    print("Choose method:")
    print("1. Open pages one by one with delay (recommended)")
    print("2. Open all pages at once in Firefox")
    print("3. Convert text URLs and open in Firefox")
    
    try:
        choice = input("Enter your choice (1, 2, or 3): ").strip()
        
        if choice == "1":
            delay = input("Enter delay between pages in seconds (default 1): ").strip()
            delay = float(delay) if delay else 1.0
            open_multiple_pages_firefox(urls_to_open, delay)
        elif choice == "2":
            open_firefox_with_multiple_tabs(urls_to_open)
        elif choice == "3":
            # Example of using convert_urls output with open_firefox_with_multiple_tabs
            print("Paste your URLs (one per line), then press Enter twice:")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            
            if lines:
                text_urls = '\n'.join(lines)
                # Convert text to list format
                list_format = convert_urls(text_urls)
                print("Converted format:")
                print(list_format)
                
                # Extract URLs from the converted format and open in Firefox
                url_list = [line.strip() for line in text_urls.split('\n') if line.strip()]
                open_firefox_with_multiple_tabs(url_list)
            else:
                print("No URLs entered.")
        else:
            print("Invalid choice. Using method 1 with default settings.")
            open_multiple_pages_firefox(urls_to_open)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {e}")