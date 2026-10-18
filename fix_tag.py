path = "Stegano.py"
src = open(path, encoding="utf-8").read()
old = "        print(f\"LOAD-DEBUG: live={self._has_live_composition()} carry={self._carry_composition}\")"
new = """        print(f"LOAD-DEBUG: live={self._has_live_composition()} carry={self._carry_composition} path={p}")"""
assert src.count(old) == 1, "DEBUG LINE NOT FOUND"
src = src.replace(old, new)
open(path, "w", encoding="utf-8").write(src)
print("TAG OK")
