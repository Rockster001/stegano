path = "Stegano.py"
src = open(path, encoding="utf-8").read()
old = """        if self._editing_layer == 2 and self._layer2_active:
            self.pwd_input.setStyleSheet("")
            self.pwd_input2.setStyleSheet(active_style)
        else:
            self.pwd_input.setStyleSheet(active_style)
            self.pwd_input2.setStyleSheet("")"""
new = """        if self.text_area.isReadOnly():
            active_layer = self._currently_shown_layer
        else:
            active_layer = self._editing_layer
        if active_layer == 2:
            self.pwd_input.setStyleSheet("")
            self.pwd_input2.setStyleSheet(active_style)
        else:
            self.pwd_input.setStyleSheet(active_style)
            self.pwd_input2.setStyleSheet("")"""
assert src.count(old) == 1, "METHOD BODY NOT FOUND EXACTLY ONCE"
src = src.replace(old, new)
open(path, "w", encoding="utf-8").write(src)
print("PATCH APPLIED OK")
