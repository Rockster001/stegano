from PyQt5.QtCore import QThread, pyqtSignal
import logging

logger = logging.getLogger("Stegano")


class EncodeWorker(QThread):
    encoding_finished = pyqtSignal(str)
    error = pyqtSignal(str)
    def __init__(self, target_fn, args, parent=None):
        super().__init__(parent)
        self.target_fn = target_fn
        self.args = args
    def run(self):
        try:
            self.target_fn(*self.args)
            self.encoding_finished.emit("OK")
        except Exception as e:
            logger.exception("Encoding failed")
            self.error.emit(str(e))

class DecodeWorker(QThread):
    decoding_finished = pyqtSignal(str, bool, int, str)
    error = pyqtSignal(str)
    def __init__(self, path, delimiter, pass1, pass2, parent=None):
        super().__init__(parent)
        self.path = path
        self.delimiter = delimiter
        self.pass1 = pass1
        self.pass2 = pass2
    def run(self):
        try:
            from steganography_utils import detect_message_format, decode_image, decode_dual_image
            fmt = detect_message_format(self.path, self.delimiter)
            if fmt == 'dual':
                msg, layer, was_encrypted, layer1_msg = decode_dual_image(self.path, self.delimiter, self.pass1, self.pass2)
                self.decoding_finished.emit(msg, was_encrypted, layer, layer1_msg)
            else:
                msg, is_encrypted = decode_image(self.path, self.delimiter, self.pass1)
                layer = 1 if msg else 0
                self.decoding_finished.emit(msg, is_encrypted, layer, msg)
        except Exception as e:
            logger.exception("Decoding failed")
            self.error.emit(str(e))

class ImageLoadWorker(QThread):
    loaded = pyqtSignal(dict)
    error = pyqtSignal(str)
    def __init__(self, path, delimiter, parent=None):
        super().__init__(parent)
        self.path = path
        self.delimiter = delimiter
    def run(self):
        try:
            from PIL import Image
            from steganography_utils import detect_message_format, decode_image, decode_dual_image, check_image_for_message
            img = Image.open(self.path).convert("RGB")
            capacity_bits = img.size[0] * img.size[1] * 3
            fmt = detect_message_format(self.path, self.delimiter)
            has_message = fmt in ('single', 'dual')
            is_encrypted = False
            message = ""
            if fmt == 'dual':
                msg, layer, was_encrypted, layer1_msg = decode_dual_image(self.path, self.delimiter, "", "")
                if layer > 0:
                    message = msg
                    is_encrypted = was_encrypted
                else:
                    is_encrypted = True
            elif fmt == 'single':
                has_message, is_encrypted = check_image_for_message(self.path, self.delimiter)
                if has_message and not is_encrypted:
                    message, _ = decode_image(self.path, self.delimiter, "")
            self.loaded.emit({
                'capacity_bits': capacity_bits,
                'has_message': has_message,
                'is_encrypted': is_encrypted,
                'message': message,
            })
        except Exception as e:
            logger.exception("Image load/scan failed")
            self.error.emit(str(e))
