"""
Remove the entire SYNONYM_MAPPING section from project_types.py
"""

# Read the file
with open('project_types.py', 'r') as f:
    lines = f.readlines()

# Find the start and end of SYNONYM_MAPPING
start_line = None
end_line = None

for i, line in enumerate(lines):
    if 'SYNONYM_MAPPING REMOVED' in line:
        start_line = i
    if start_line is not None and line.strip() == '}' and i > start_line + 10:
        end_line = i
        break

if start_line is not None and end_line is not None:
    print(f"Found SYNONYM_MAPPING section from line {start_line+1} to {end_line+1}")
elif start_line is not None:
    print(f"Found start at line {start_line+1} but no end")
else:
    print("Could not find SYNONYM_MAPPING section")

# Remove the synonym mapping section
if start_line is not None and end_line is not None:
    # Keep everything before synonym mapping, replace with comment, keep everything after
    new_lines = (
        lines[:start_line] + 
        ['# SYNONYM MAPPING REMOVED - LLM handles all intelligence via enum constraint\n', '\n'] +
        lines[end_line+1:]
    )
    
    # Write back
    with open('project_types.py', 'w') as f:
        f.writelines(new_lines)
    
    print(f"Removed {end_line - start_line + 1} lines of synonym mapping code")
    print("LLM will now handle all categorization intelligence!")
else:
    print("Could not find SYNONYM_MAPPING section boundaries")