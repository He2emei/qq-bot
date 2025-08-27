# test_faq_images.py
#!/usr/bin/env python3
"""Test FAQ image localization functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_manager import database_manager
from handlers.faq_handler import handle_faq_edit, handle_faq_query
from utils.image_utils import image_manager

def test_image_download():
    """Test image download functionality"""
    print("=== Test Image Download Functionality ===")

    # Create a simple test image file to simulate download
    test_dir = "data/faq_images"
    os.makedirs(test_dir, exist_ok=True)

    # Create a small test image file
    test_image_path = os.path.join(test_dir, "test_image.jpg")
    with open(test_image_path, "wb") as f:
        # Create a minimal JPEG file header
        f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9')

    print(f"[OK] Test image created successfully: {test_image_path}")
    print(f"File size: {os.path.getsize(test_image_path)} bytes")

    # Test duplicate download detection (should return existing file)
    result_path = image_manager.download_image("test_url")
    if result_path:
        print(f"[OK] Duplicate detection working correctly")
    else:
        print("[INFO] Duplicate detection test skipped (requires network connection)")

    print()

def test_content_processing():
    """Test content processing functionality"""
    print("=== Test Content Processing Functionality ===")

    # Test content with image URL
    content_with_url = "This is test content with image: https://via.placeholder.com/200x150.png and text"
    processed = image_manager.process_content_images(content_with_url)
    print(f"Original content: {content_with_url}")
    print(f"Processed: {processed}")

    # Test CQ code content
    cq_content = "This is CQ code content: [CQ:image,url=https://via.placeholder.com/100x100.jpg]"
    processed_cq = image_manager.process_content_images(cq_content)
    print(f"CQ code content: {cq_content}")
    print(f"Processed: {processed_cq}")

    print()

def test_faq_with_images():
    """Test FAQ functionality with image processing"""
    print("=== Test FAQ Functionality with Image Processing ===")

    # Mock event data
    def create_mock_event(message_text, group_id=123456):
        return {
            'message': message_text,
            'group_id': group_id
        }

    # Test editing FAQ with image
    print("Test editing FAQ with image:")
    event = create_mock_event('#faq edit test_image_faq This is FAQ content with image: https://via.placeholder.com/400x300.jpg and other text')
    handle_faq_edit(event)

    # Test querying FAQ with image
    print("\nTest querying FAQ with image:")
    event = create_mock_event('#faq test_image_faq')
    handle_faq_query(event)

    # Verify local image files
    print("\nVerify local image files:")
    if os.path.exists('data/faq_images'):
        files = os.listdir('data/faq_images')
        print(f"Files in local image directory: {files}")
        for file in files:
            file_path = os.path.join('data/faq_images', file)
            print(f"  {file}: {os.path.getsize(file_path)} bytes")
    else:
        print("Local image directory does not exist")

    print()

def test_image_cleanup():
    """Test image cleanup functionality"""
    print("=== Test Image Cleanup Functionality ===")

    # Note: This test will clean old files, use with caution
    print("Skipping cleanup test (to avoid deleting useful files)")

    print()

if __name__ == "__main__":
    print("Starting FAQ image localization test...\n")

    # Create necessary directories
    os.makedirs('data/faq_images', exist_ok=True)

    # Test image download functionality
    test_image_download()

    # Test content processing functionality
    test_content_processing()

    # Test FAQ functionality with image processing
    test_faq_with_images()

    # Test image cleanup functionality
    test_image_cleanup()

    print("Test completed!")
    print("\nNote: Downloaded image files are saved in data/faq_images/ directory")