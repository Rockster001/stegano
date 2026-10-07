path = "Stegano.py"
src = open(path, encoding="utf-8").read()
old = """                if obj is self.pwd_input:
                    self._switch_to_layer(1)
                    if not self.text_area.isReadOnly():
                        self._update_pass_field_highlight()
                elif obj is self.pwd_input2 and (self._layer2_active or self.text_area.isReadOnly()):
                    self._switch_to_layer(2)
                    if not self.text_area.isReadOnly():
                        self._update_pass_field_highlight()"""
new = """                if obj is self.pwd_input:
                    self._switch_to_layer(1)
                    self._update_pass_field_highlight()
                elif obj is self.pwd_input2 and (self._layer2_active or self.text_area.isReadOnly()):
                    self._switch_to_layer(2)
                    self._update_pass_field_highlight()"""
assert src.count(old) == 1, "EVENTFILTER BLOCK NOT FOUND EXACTLY ONCE"
src = src.replace(old, new)
open(path, "w", encoding="utf-8").write(src)
print("PATCH APPLIED OK")
