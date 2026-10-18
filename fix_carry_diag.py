path = "Stegano.py"
src = open(path, encoding="utf-8").read()
old1 = "        self._carry_composition = False"
new1 = "        self._carry_composition = False\n        print(\"CARRY-SET: False (in _select_image)\")"
old2 = "        self._carry_composition = True"
new2 = "        self._carry_composition = True\n        print(\"CARRY-SET: True\")"
assert src.count(old1) == 1, "FALSE-SET NOT FOUND"
n = src.count(old2)
assert n >= 1, "TRUE-SET NOT FOUND"
src = src.replace(old2, new2)
open(path, "w", encoding="utf-8").write(src)
print(f"INSTRUMENTED OK - {n} True-set sites instrumented")
