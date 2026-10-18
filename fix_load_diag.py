path = "Stegano.py"
src = open(path, encoding="utf-8").read()
old = "        # Preserve composition if live and carry_composition is True"
new = """        # Preserve composition if live and carry_composition is True
        print(f"LOAD-DEBUG: live={self._has_live_composition()} carry={self._carry_composition}")"""
assert src.count(old) == 1, "ANCHOR NOT FOUND"
src = src.replace(old, new)
open(path, "w", encoding="utf-8").write(src)
print("DIAGNOSTIC OK")
