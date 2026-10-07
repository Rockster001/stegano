path = "Stegano.py"
src = open(path, encoding="utf-8").read()
old = """        if self.text_area.isReadOnly():
            active_layer = self._currently_shown_layer
        else:
            active_layer = self._editing_layer"""
new = old + """
        print(f"HL-DEBUG: readonly={self.text_area.isReadOnly()} shown={self._currently_shown_layer} editing={self._editing_layer} layer2_active={self._layer2_active} -> active_layer={active_layer}")"""
assert src.count(old) == 1, "DIAGNOSTIC ANCHOR NOT FOUND"
src = src.replace(old, new)
open(path, "w", encoding="utf-8").write(src)
print("DIAGNOSTIC INSERTED OK")
