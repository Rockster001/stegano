path = "Stegano.py"
src = open(path, encoding="utf-8").read()
old = "self.pwd_input2.returnPressed.connect(self._attempt_decode)"
assert src.count(old) == 1, "CONNECTION NOT FOUND"
src = src.replace(old, "self.pwd_input2.returnPressed.connect(self._on_pass2_enter)")
lines = []
lines.append("    def _on_pass2_enter(self):")
lines.append("        if self.worker_running:")
lines.append("            return")
lines.append("        decoded = self.text_area.isReadOnly() and self._currently_shown_layer >= 1")
lines.append("        pass1 = self.pwd_input.text()")
lines.append("        pass2 = self.pwd_input2.text()")
lines.append("        if decoded:")
lines.append("            if pass2:")
lines.append("                self._attempt_decode()")
lines.append("        else:")
lines.append("            if not pass1:")
lines.append("                self._status('Enter Pass 1 to encode.', 'error')")
lines.append("            elif pass2:")
lines.append("                self._encode_msg()")
method = chr(10).join(lines)
anchor = "    def _attempt_decode(self):"
assert src.count(anchor) == 1, "ANCHOR NOT FOUND"
src = src.replace(anchor, method + chr(10) + anchor)
open(path, "w", encoding="utf-8").write(src)
print("PATCH APPLIED OK")
