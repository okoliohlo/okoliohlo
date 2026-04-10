"""Simple script to run get_token_via_api()"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from business.api.api_helpers import get_token_via_api

print("=" * 80)
print("RUNNING get_token_via_api()")
print("=" * 80)

# Run the function
auth_data = get_token_via_api('staging', 'standard')

print("\n" + "=" * 80)
print("AUTHENTICATION RESULT")
print("=" * 80)
print(f"\nUsername: {auth_data['username']}")
print(f"Auth Token Type: {auth_data['auth_token']}")
print(f"Cookies Count: {len(auth_data['cookies'])}")

print("\n" + "=" * 80)
print("COOKIES")
print("=" * 80)
for cookie_name, cookie_value in auth_data['cookies'].items():
    if len(cookie_value) > 80:
        print(f"{cookie_name}: {cookie_value[:80]}...")
    else:
        print(f"{cookie_name}: {cookie_value}")

print("\n" + "=" * 80)
print("SUCCESS - Token retrieved!")
print("=" * 80)
