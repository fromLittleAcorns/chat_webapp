"""
Quick script to check what HTMX version FastHTML provides
"""
from fasthtml.common import *
from monsterui.all import *

# Check FastHTML's default headers
print("=" * 60)
print("Checking FastHTML HTMX version...")
print("=" * 60)

# Get Theme headers
theme_headers = Theme.blue.headers()

print(f"\nTheme.blue.headers() contains {len(theme_headers)} items:\n")

for i, header in enumerate(theme_headers):
    print(f"{i+1}. {header}")
    
print("\n" + "=" * 60)
print("Look for 'htmx' in the URLs above")
print("=" * 60)
