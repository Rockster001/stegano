import subprocess

HEAD_SRC = subprocess.run(
    ["git", "-C", r"C:\Dev\Stegano", "show", "HEAD:Stegano.py"],
    capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
assert HEAD_SRC, "could not read HEAD:Stegano.py from git"

def extract_func(src, name):
    marker = "    def %s(self):" % name
    i = src.find(marker)
    assert i != -1, "function %s not found" % name
    j = src.find("\n    def ", i + 1)
    j = j if j != -1 else len(src)
    return src[i:j].rstrip() + "\n"

head_init_ui = extract_func(HEAD_SRC, "_init_ui")

BK = r"C:\Dev\Stegano\Stegano_broken_backup.py"
src = open(BK, encoding="utf-8").read()
assert "STEALTH_HEADER = hashlib.sha256" in src, "backup lacks header aliases - wrong file?"
cur_init_ui = extract_func(src, "_init_ui")
assert "_setup_main_layout" not in cur_init_ui, "backup already repaired?"
assert head_init_ui != cur_init_ui, "no graft needed?"

out = src.replace(cur_init_ui, head_init_ui, 1)
assert out != src and out.count("def _init_ui") == 1

open(r"C:\Dev\Stegano\Stegano.py", "w", encoding="utf-8").write(out)
print("OK - grafted original _init_ui (%d lines) into Stegano.py" % head_init_ui.count("\n"))
print("Backup untouched. Now run:  python stegano.py")
