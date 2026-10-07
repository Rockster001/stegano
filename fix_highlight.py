path = "Stegano.py"
src = open(path, encoding="utf-8").read()
old = "        if self._editing_layer == 2 and self._layer2_active:"
new = (
    "        if self.text_area.isReadOnly():\n"
    "            active_layer = self._currently_shown_layer\n"
    "        else:\n"
    "            active_layer = self._editing_layer\n"
    "        if active_layer == 2 and self._layer2_active:"
)
assert src.count(old) == 1, "CONDITION LINE NOT FOUND EXACTLY ONCE"
src = src.replace(old, new)
open(path, "w", encoding="utf-8").write(src)
print("PATCH APPLIED OK")
