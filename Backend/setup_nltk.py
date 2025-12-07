#!/usr/bin/env python3
"""
Standalone script to download NLTK data
Run this once to set up NLTK resources for the application
"""

import nltk
import sys

def download_nltk_resources():
    """Download all required NLTK resources"""
    print("🔍 Checking and downloading NLTK resources...\n")
    
    resources = [
        ('punkt_tab', 'tokenizers/punkt_tab'),  # Try newer version first
        ('punkt', 'tokenizers/punkt'),          # Fallback to older version
        ('averaged_perceptron_tagger', 'taggers/averaged_perceptron_tagger'),
    ]
    
    success_count = 0
    
    for resource_name, resource_path in resources:
        try:
            nltk.data.find(resource_path)
            print(f"✅ {resource_name} - already available")
            success_count += 1
        except LookupError:
            try:
                print(f"📥 Downloading {resource_name}...")
                nltk.download(resource_name, quiet=False)
                print(f"✅ {resource_name} - downloaded successfully\n")
                success_count += 1
            except Exception as e:
                print(f"❌ {resource_name} - failed: {e}\n")
    
    if success_count > 0:
        print(f"\n✅ Successfully set up {success_count}/{len(resources)} NLTK resources")
        return True
    else:
        print("\n❌ Failed to set up NLTK resources")
        return False

if __name__ == "__main__":
    try:
        success = download_nltk_resources()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Download interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
