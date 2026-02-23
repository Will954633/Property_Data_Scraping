#!/usr/bin/env python3
with open("run_parallel_suburb_scrape.py", "r") as f:
    lines = f.readlines()

# Find the line with "except Exception as e:" in save_to_mongodb function
for i, line in enumerate(lines):
    if i > 580 and i < 630 and "except Exception as e:" in line:
        # Check if logging already added
        if i+1 < len(lines) and "Database save error" not in lines[i+1]:
            # Add logging after except line
            indent = " " * 12
            lines.insert(i+1, f"{indent}self.log(f\"❌ Database save error: {{e}}\")\n")
            print(f"Added logging at line {i+1}")
            break

with open("run_parallel_suburb_scrape.py", "w") as f:
    f.writelines(lines)
    
print("✅ Logging added successfully")
