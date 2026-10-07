path = "Stegano.py"
src = open(path, encoding="utf-8").read()
old = "        self._editing_layer = target\n"
new = "        self._editing_layer = target\n        self._currently_shown_layer = target\n"
assert src.count(old) == 1, "SWITCH LINE NOT FOUND EXACTLY ONCE"
src = src.replace(old, new)
open(path, "w", encoding="utf-8").write(src)
print("PATCH APPLIED OK")
