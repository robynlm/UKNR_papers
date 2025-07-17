#!/usr/bin/env python3
"""
Test script to verify the arXiv scraper works correctly
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import requests
        print("✓ requests library found")
    except ImportError:
        print("✗ requests library not found")
        return False
    
    return True

def test_scraper():
    """Test the arXiv scraper with a small query."""
    print("\n" + "="*50)
    print("Testing arXiv scraper...")
    print("="*50)
    
    try:
        # Run with limited results for testing
        result = subprocess.run([
            sys.executable, "arxiv_scraper.py", 
            "--days-back", "7", 
            "--max-results", "5",
            "--output", "test_output.html"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✓ Scraper ran successfully")
            print("Output:", result.stdout)
            
            # Check if HTML file was created
            if os.path.exists("test_output.html"):
                print("✓ HTML file generated successfully")
                with open("test_output.html", "r") as f:
                    content = f.read()
                    if "Numerical Relativity Papers" in content:
                        print("✓ HTML content looks correct")
                        file_size = len(content)
                        print(f"✓ Generated file size: {file_size} characters")
                    else:
                        print("✗ HTML content appears incomplete")
                
                # Clean up test file
                os.remove("test_output.html")
                print("✓ Test file cleaned up")
            else:
                print("✗ HTML file was not generated")
        else:
            print("✗ Scraper failed to run")
            print("Error:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Scraper timed out")
        return False
    except Exception as e:
        print(f"✗ Error running scraper: {e}")
        return False
    
    return True

def main():
    """Main test function."""
    print("Numerical Relativity Papers - Setup Test")
    print("="*50)
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 6):
        print(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print("✗ Python 3.6+ required")
        return
    
    # Check if we're in the right directory
    if os.path.exists("arxiv_scraper.py"):
        print("✓ arxiv_scraper.py found")
    else:
        print("✗ arxiv_scraper.py not found - make sure you're in the right directory")
        return
    
    # Check dependencies
    if not check_dependencies():
        print("\nInstall dependencies with: pip install -r requirements.txt")
        return
    
    # Test the scraper
    if test_scraper():
        print("\n" + "="*50)
        print("✓ ALL TESTS PASSED!")
        print("="*50)
        print("\nYour setup is ready!")
        print("\nNext steps:")
        print("1. Push this repository to GitHub")
        print("2. Enable GitHub Pages in repository settings")
        print("3. Enable GitHub Actions")
        print("4. The page will be available at: https://yourusername.github.io/UKNR_papers/")
    else:
        print("\n" + "="*50)
        print("✗ SOME TESTS FAILED")
        print("="*50)
        print("Please check the errors above and try again.")

if __name__ == "__main__":
    main()
