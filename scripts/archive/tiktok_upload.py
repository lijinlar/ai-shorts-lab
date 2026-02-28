"""
TikTok Upload Automation
Uploads videos to TikTok programmatically using selenium-based automation
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Chrome profile path (managed browser)
CHROME_PROFILE = r"C:\Users\lijin\AppData\Local\Google\Chrome\User Data"
PROFILE_DIRECTORY = "Default"

class TikTokUploader:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Initialize Chrome with existing profile"""
        options = Options()
        options.add_argument(f"user-data-dir={CHROME_PROFILE}")
        options.add_argument(f"profile-directory={PROFILE_DIRECTORY}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Use existing Chrome instance
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)
        
    def upload_video(self, video_path, title, description="", hashtags=None):
        """Upload a single video to TikTok"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Navigate to upload page
        self.driver.get("https://www.tiktok.com/tiktokstudio/upload")
        time.sleep(3)
        
        # Find and upload file
        file_input = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
        )
        file_input.send_keys(str(Path(video_path).absolute()))
        
        # Wait for upload to process
        print(f"Uploading {Path(video_path).name}...")
        time.sleep(10)  # Wait for video processing
        
        # Fill in caption
        caption_field = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
        )
        
        # Build caption with hashtags
        caption_text = title
        if description:
            caption_text += f"\n\n{description}"
        if hashtags:
            caption_text += f"\n\n{' '.join(hashtags)}"
        
        caption_field.click()
        caption_field.send_keys(caption_text)
        
        time.sleep(2)
        
        # Click post button
        post_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Post')]"))
        )
        post_button.click()
        
        # Wait for upload to complete
        print("Posting...")
        time.sleep(10)
        
        return True
        
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()


def tiktok_optimize_title(youtube_title):
    """Convert YouTube title to TikTok-friendly format"""
    # Remove emoji from start, make more casual
    title = youtube_title.replace("🐕💔", "").replace("🦮❤️", "").replace("🐶😢", "").replace("🐕‍🦺💪", "")
    title = title.replace("#shorts", "").strip()
    
    # Make more casual for TikTok
    title = title.replace("...", "!")
    title = title.replace(" — ", " - ")
    
    return title[:150]  # TikTok limit


def get_tiktok_hashtags():
    """Get popular TikTok hashtags for dog content"""
    return [
        "#dogsoftiktok",
        "#dogrescue",
        "#wholesomedog",
        "#rescuedog",
        "#fyp",
        "#viral",
        "#dogstory",
        "#heartwarming"
    ]


def main():
    """Upload today's videos to TikTok"""
    workspace = Path(__file__).parent.parent
    series_dir = workspace / "out" / "series"
    
    # Get today's videos
    videos = list(series_dir.glob("*.mp4"))
    videos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not videos:
        print("❌ No videos found to upload")
        return
    
    # Take latest 4 videos
    videos_to_upload = videos[:4]
    
    print(f"📹 Found {len(videos_to_upload)} videos to upload")
    
    uploader = TikTokUploader()
    
    try:
        uploader.setup_driver()
        
        results = []
        for video_path in videos_to_upload:
            # Generate title from filename
            title = video_path.stem.replace("-", " ").replace("_", " ").title()
            title = tiktok_optimize_title(title)
            
            hashtags = get_tiktok_hashtags()
            
            print(f"\n📤 Uploading: {video_path.name}")
            print(f"📝 Title: {title}")
            
            try:
                success = uploader.upload_video(
                    str(video_path),
                    title=title,
                    hashtags=hashtags
                )
                
                results.append({
                    "video": video_path.name,
                    "title": title,
                    "status": "success" if success else "failed",
                    "timestamp": datetime.now().isoformat()
                })
                
                print(f"✅ Uploaded: {video_path.name}")
                
                # Wait between uploads
                time.sleep(30)
                
            except Exception as e:
                print(f"❌ Failed to upload {video_path.name}: {e}")
                results.append({
                    "video": video_path.name,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Save results
        report_path = workspace / "out" / "tiktok_reports" / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, "w") as f:
            json.dump({
                "date": datetime.now().isoformat(),
                "total": len(videos_to_upload),
                "successful": sum(1 for r in results if r["status"] == "success"),
                "results": results
            }, f, indent=2)
        
        print(f"\n✅ Upload complete! Report saved to {report_path}")
        
    finally:
        uploader.close()


if __name__ == "__main__":
    main()
