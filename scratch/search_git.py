import os

git_dir = "c:\\Personal\\Projects\\systematic\\systematic\\.git"

print("Searching .git directory for credentials...")
found = False

for root, dirs, files in os.walk(git_dir):
    for file in files:
        # Skip binary files that are too big
        if file in ["index", "pack"]:
            continue
        path = os.path.join(root, file)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "password" in content.lower() or "sbp_" in content or "postgres:" in content or "postgresql" in content:
                    print(f"\nPossible credentials found in: {path}")
                    for line in content.splitlines():
                        if any(x in line for x in ["password", "sbp_", "postgres:", "postgresql"]):
                            print("  ", line.strip())
                            found = True
        except Exception as e:
            pass

if not found:
    print("No credentials found in .git history.")
