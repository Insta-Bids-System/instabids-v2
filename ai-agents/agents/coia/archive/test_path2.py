import pathlib

# Check from tools.py location
file_path = pathlib.Path(__file__)
print(f"Current file: {file_path}")
print(f"Parent (coia): {file_path.parent}")
print(f"Parent.parent (agents): {file_path.parent.parent}")
print(f"Parent.parent.parent (ai-agents): {file_path.parent.parent.parent}")

# Try to find .env
root_env = file_path.parent.parent.parent / '.env'
print(f"\nTrying: {root_env}")
print(f"Exists: {root_env.exists()}")