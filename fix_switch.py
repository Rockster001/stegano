path = "Stegano.py"
src = open(path, encoding="utf-8").read()
old = """        self._editing_layer = target
        if self.text_area.isReadOnly():
            if target == 1:
                self.text_area.setHtml(convert_links_to_html(self._decoded_layer1_message))
            else:
                self.text_area.setHtml(convert_links_to_html(self._decoded_layer2_message))
        else:
            self.text_area.setPlainText(self._message1_buffer if target == 1 else
self._message2_buffer)"""
new = """        self._editing_layer = target
        self._currently_shown_layer = target
        if self.text_area.isReadOnly():
            if target == 1:
                self.text_area.setHtml(convert_links_to_html(self._decoded_layer1_message))
            else:
                self.text_area.setHtml(convert_links_to_html(self._decoded_layer2_message))
        else:
            self.text_area.setPlainText(self._message1_buffer if target == 1 else
self._message2_buffer)"""
assert src.count(old) == 1, "SWITCH BODY NOT FOUND EXACTLY ONCE"
src = src.replace(old, new)
open(path, "w", encoding="utf-8").write(src)
print("PATCH APPLIED OK")
