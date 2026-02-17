#!/usr/bin/env python3
print("Testing imports...")

try:
    from config import Config
    print("✅ config.py")
except Exception as e:
    print(f"❌ config.py: {e}")

try:
    from database import db
    print("✅ database.py")
except Exception as e:
    print(f"❌ database.py: {e}")

try:
    from utils import keyboards
    print("✅ utils/keyboards.py")
except Exception as e:
    print(f"❌ utils/keyboards.py: {e}")

try:
    from utils import helpers
    print("✅ utils/helpers.py")
except Exception as e:
    print(f"❌ utils/helpers.py: {e}")

try:
    from plugins import broadcast
    print("✅ plugins/broadcast.py")
except Exception as e:
    print(f"❌ plugins/broadcast.py: {e}")

try:
    from plugins import groups
    print("✅ plugins/groups.py")
except Exception as e:
    print(f"❌ plugins/groups.py: {e}")

print("\nDone!")
