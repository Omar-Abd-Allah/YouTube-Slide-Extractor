"""
╔══════════════════════════════════════════════════════════════════╗
║         YouTube Slide Extractor — Auto Screenshot Tool           ║
║                                                                  ║
║  Automatically captures screenshots from any YouTube video       ║
║  at custom intervals and exports them as a clean PDF.            ║
║                                                                  ║
║  Author  : [Omar Abd Allah Kamel]                                ║
║  Requires: pip install yt-dlp opencv-python pillow               ║
╚══════════════════════════════════════════════════════════════════╝
"""
import cv2
import os
import sys
import time
from PIL import Image
import yt_dlp
 
 
# ═══════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
 
OUTPUT_FOLDER = "slides"
OUTPUT_PDF    = "slides.pdf"
QUALITY       = "worst[ext=mp4]"   # Lowest quality = fastest
 
 
# ═══════════════════════════════════════════════════════════════════
#  STEP 0 — Ask user for settings
# ═══════════════════════════════════════════════════════════════════
 
def get_user_settings() -> tuple:
    """
    how many seconds they want between each screenshot.
    """
    print("═" * 60)
    print("   🎬  YouTube Slide Extractor")
    print("═" * 60)
    print()
 
    # ── Get URL ───────────────────────────────────────────────────
    while True:
        url = input("  📺  Paste YouTube URL: ").strip()
        if url.startswith("http") and "youtube" in url or "youtu.be" in url:
            break
        print("  ⚠   That doesn't look like a YouTube URL. Try again.\n")
 
    # ── Get interval ──────────────────────────────────────────────
    print()
    print("  ⏱   How many seconds between each screenshot?")
    print()
    print("       [1]  Every 30 seconds  — very detailed, lots of slides")
    print("       [2]  Every 60 seconds  — balanced  (recommended)")
    print("       [3]  Every 120 seconds — fewer slides, runs faster")
    print("       [4]  Custom — enter your own number")
    print()
 
    preset_map = {"1": 30, "2": 60, "3": 120}
 
    while True:
        choice = input("  Choose [1/2/3/4]: ").strip()
 
        if choice in preset_map:
            interval = preset_map[choice]
            break
 
        elif choice == "4":
            while True:
                try:
                    custom = int(input("  Enter seconds (e.g. 45): ").strip())
                    if 5 <= custom <= 600:
                        interval = custom
                        break
                    else:
                        print("  ⚠   Please enter a number between 5 and 600.")
                except ValueError:
                    print("  ⚠   Please enter a valid number.")
            break
 
        else:
            print("  ⚠   Please enter 1, 2, 3, or 4.")
 
    # ── Get output PDF name ───────────────────────────────────────
    print()
    default_pdf = "slides.pdf"
    custom_pdf  = input(f"  📄  Output PDF name (press Enter for '{default_pdf}'): ").strip()
    pdf_name    = custom_pdf if custom_pdf.endswith(".pdf") else (
                  custom_pdf + ".pdf" if custom_pdf else default_pdf)
 
    return url, interval, pdf_name
 
 
# ═══════════════════════════════════════════════════════════════════
#  STEP 1 — Get video URL
# ═══════════════════════════════════════════════════════════════════
 
def get_stream_info(url: str) -> tuple:
    """
    Extract the direct URL and metadata from a YouTube link.
    No video file is downloaded — we only get the URL.
    """
    print("\n  📡  Connecting to YouTube...")
 
    ydl_opts = {
        "format":      QUALITY,
        "quiet":       True,
        "no_warnings": True,
    }
 
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info       = ydl.extract_info(url, download=False)
        stream_url = info["url"]
        duration   = info.get("duration", 0)
        title      = info.get("title", "Unknown Title")
        channel    = info.get("uploader", "Unknown Channel")
 
    return stream_url, duration, title, channel
 
 
# ═══════════════════════════════════════════════════════════════════
#  STEP 2 — Capture frames at chosen interval
# ═══════════════════════════════════════════════════════════════════
 
def capture_slides(stream_url: str, duration: int, interval: int) -> list:
    """
    Seeks through the video at every interval seconds
    and saves a screenshot — without buffering the full video.
    """
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
 
    total_slides = duration // interval
    saved_paths  = []
    cap          = cv2.VideoCapture(stream_url)
 
    if not cap.isOpened():
        print("\n  ❌  Could not open video. Check your internet connection.")
        sys.exit(1)
 
    print(f"\n  📸  Capturing 1 screenshot every {interval} seconds...")
    print(f"      Estimated screenshots: ~{total_slides}\n")
    start_time = time.time()
 
    for i, timestamp in enumerate(range(0, duration, interval)):
 
        # Seek directly to timestamp — no buffering in between
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ret, frame = cap.read()
 
        if not ret:
            continue
 
        # Filename includes both index and video timestamp
        hours   = timestamp // 3600
        minutes = (timestamp % 3600) // 60
        seconds = timestamp % 60
        filename = (
            f"{OUTPUT_FOLDER}/slide_{i:04d}_"
            f"{hours:02d}h{minutes:02d}m{seconds:02d}s.jpg"
        )
 
        cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        saved_paths.append(filename)
 
        # Progress update every 10 slides
        if (i + 1) % 10 == 0 or i == 0:
            elapsed   = time.time() - start_time
            progress  = (i + 1) / max(total_slides, 1) * 100
            eta_secs  = (elapsed / (i + 1)) * (total_slides - i - 1)
            eta_min   = int(eta_secs // 60)
            eta_sec   = int(eta_secs % 60)
            print(
                f"    [{progress:5.1f}%]  Slide {i+1:4d} / ~{total_slides}"
                f"   |   ⏱  ETA: {eta_min}m {eta_sec}s"
                f"   |   🕐 {hours:02d}:{minutes:02d}:{seconds:02d}"
            )
 
    cap.release()
    return saved_paths
 
 
# ═══════════════════════════════════════════════════════════════════
#  STEP 3 — Combine all screenshots into one PDF
# ═══════════════════════════════════════════════════════════════════
 
def build_pdf(image_paths: list, output_pdf: str, title: str):
    """
    Converts all captured JPEG screenshots into 
    a single multi-page PDF using Pillow.
    """
    print(f"\n  📄  Building PDF from {len(image_paths)} slides...")
 
    valid_images = []
    for path in sorted(image_paths):
        try:
            img = Image.open(path).convert("RGB")
            valid_images.append(img)
        except Exception as e:
            print(f"    ⚠  Skipping {path}: {e}")
 
    if not valid_images:
        print("  ❌  No valid images found. PDF not created.")
        return
 
    valid_images[0].save(
        output_pdf,
        save_all=True,
        append_images=valid_images[1:],
        title=title,
    )
 
    size_mb = os.path.getsize(output_pdf) / (1024 * 1024)
    print(f"    ✅  Saved: {output_pdf}  ({size_mb:.1f} MB)")
 
 
# ═══════════════════════════════════════════════════════════════════
#  STEP 4 — Print final summary
# ═══════════════════════════════════════════════════════════════════
 
def print_summary(title: str, channel: str, slide_count: int,
                  duration: int, interval: int, pdf_path: str, elapsed: float):
 
    run_h  = int(elapsed // 3600)
    run_m  = int((elapsed % 3600) // 60)
    run_s  = int(elapsed % 60)
    vid_h  = duration // 3600
    vid_m  = (duration % 3600) // 60
 
    print("\n" + "═" * 60)
    print("  ✅  ALL DONE!")
    print("═" * 60)
    print(f"    Video    : {title}")
    print(f"    Channel  : {channel}")
    print(f"    Duration : {vid_h}h {vid_m}m")
    print(f"    Interval : every {interval} seconds")
    print(f"    Slides   : {slide_count} screenshots captured")
    print(f"    PDF      : {pdf_path}")
    print(f"    Runtime  : {run_h:02d}h {run_m:02d}m {run_s:02d}s")
    print("═" * 60)
    print(f"\n    Slides folder : ./{OUTPUT_FOLDER}/")
    print(f"    PDF file      : ./{pdf_path}\n")
 
 
# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════
 
def main():
    total_start = time.time()
 
    # Step 0: Ask user for settings
    url, interval, pdf_name = get_user_settings()
 
    # Step 1: Get stream info
    stream_url, duration, title, channel = get_stream_info(url)
 
    # Show summary before starting
    vid_h      = duration // 3600
    vid_m      = (duration % 3600) // 60
    estimated  = duration // interval
 
    print()
    print("  ─" * 30)
    print(f"    Title    : {title}")
    print(f"    Channel  : {channel}")
    print(f"    Duration : {vid_h}h {vid_m}m")
    print(f"    Interval : every {interval} seconds")
    print(f"    Expected : ~{estimated} screenshots")
    print(f"    PDF name : {pdf_name}")
    print("  ─" * 30)
    print()
 
    answer = input("  Ready to start? (y/n): ").strip().lower()
    if answer != "y":
        print("\n  Cancelled. Goodbye!\n")
        sys.exit(0)
 
    # Step 2: Capture slides
    saved_paths = capture_slides(stream_url, duration, interval)
 
    # Step 3: Build PDF
    build_pdf(saved_paths, pdf_name, title)
 
    # Step 4: Summary
    print_summary(title, channel, len(saved_paths),
                  duration, interval, pdf_name, time.time() - total_start)
 
 
if __name__ == "__main__":
    main()
 
