_COMMON_WEAK_WORDS = {
    "password", "letmein", "login", "admin", "welcome", "qwerty", "dragon",
    "master", "shadow", "monkey", "sunshine", "princess", "football",
    "baseball", "iloveyou", "trustno1", "superman", "batman", "starwars",
    "freedom", "whatever", "hunter", "killer", "george", "jennifer",
    "michael", "jordan", "hannah", "thomas", "robert", "daniel", "william",
    "charlie", "ninja", "pokemon", "minecraft", "summer", "winter",
    "spring", "autumn", "monday", "friday", "computer", "internet",
    "changeme", "default", "guest", "test", "temp", "secret", "abc",
    "abcd", "abcde", "abcdef", "access", "flower", "purple", "orange",
    "yellow", "cricket", "soccer", "hockey", "tennis", "chelsea",
    "arsenal", "liverpool", "united", "eagles", "cowboys", "yankees",
}

_KEYBOARD_ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm", "1234567890"]

def _has_repeated_char_run(password, run_length=3):
    count = 1
    for i in range(1, len(password)):
        if password[i] == password[i - 1]:
            count += 1
            if count >= run_length:
                return True
        else:
            count = 1
    return False

def _has_sequential_run(password, run_length=3):
    if len(password) < run_length:
        return False
    for i in range(len(password) - run_length + 1):
        chunk = password[i:i + run_length]
        ascending = all(ord(chunk[j + 1]) - ord(chunk[j]) == 1 for j in range(len(chunk) - 1))
        descending = all(ord(chunk[j]) - ord(chunk[j + 1]) == 1 for j in range(len(chunk) - 1))
        if ascending or descending:
            return True
    return False

def _has_keyboard_pattern(password, min_len=4):
    lowered = password.lower()
    for row in _KEYBOARD_ROWS:
        for i in range(len(row) - min_len + 1):
            chunk = row[i:i + min_len]
            if chunk in lowered or chunk[::-1] in lowered:
                return True
    return False

def _extract_alpha_runs(password):
    runs, current = [], ""
    for c in password:
        if c.isalpha():
            current += c
        else:
            if current: runs.append(current)
            current = ""
    if current: runs.append(current)
    return runs

def _has_common_word(password):
    return any(run.lower() in _COMMON_WEAK_WORDS for run in _extract_alpha_runs(password) if len(run) >= 4)

def _has_pattern_weakness(password):
    return (_has_common_word(password) or _has_keyboard_pattern(password)
            or _has_repeated_char_run(password) or _has_sequential_run(password))

def estimate_password_strength(password):
    if not password:
        return 0
    length_score = min(len(password), 20) / 20 * 60
    upper = sum(1 for c in password if c.isupper())
    digit = sum(1 for c in password if c.isdigit())
    symbol = sum(1 for c in password if not c.isalnum())
    diversity_score = sum(min(count, 3) / 3 * (40 / 3) for count in (upper, digit, symbol))
    score = length_score + diversity_score
    if _has_pattern_weakness(password):
        score = min(score, 30)
    return min(int(round(score)), 100)

def _password_strength_tier(score):
    if score <= 0: return 0
    if score < 20: return 1
    if score < 40: return 2
    if score < 60: return 3
    if score < 80: return 4
    return 5

class PasswordStrengthMeter(QWidget):
    TIER_COLORS = ["#666666", "#FF4444", "#FF4444", "#FFA500", "#4CAF50", "#4CAF50"]
    TIER_LABELS = ["No password", "Very Weak", "Weak", "Fair", "Strong", "Very Strong"]
    BOX_COUNT = 5
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        self.boxes = []
        for _ in range(self.BOX_COUNT):
            box = QLabel()
            box.setFixedSize(14, 10)
            box.setStyleSheet("background-color: rgba(100, 100, 100, 0.3); border-radius: 2px;")
            layout.addWidget(box)
            self.boxes.append(box)
    def update_strength(self, password):
        score = estimate_password_strength(password)
        tier = _password_strength_tier(score)
        color = self.TIER_COLORS[tier]
        for i, box in enumerate(self.boxes):
            if i < tier:
                box.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
            else:
                box.setStyleSheet("background-color: rgba(100, 100, 100, 0.3); border-radius: 2px;")
        self.setToolTip(self.TIER_LABELS[tier])

class SavedPasswordsDialog(QDialog):
    def __init__(self, passwords, parent=None):
        super().__init__(parent)
        self.passwords = list(passwords)
        self.selected_password = None
        self.setWindowTitle("Saved Passwords")
        self.setFixedSize(400, 350)
        self._init_ui()
        self._populate_list()
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        header = QLabel("Double-click a password to use it, or select and click Use")
        header.setStyleSheet("font-size: 12px; color: #888; margin-bottom: 5px;")
        layout.addWidget(header)
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_use)
        layout.addWidget(self.list_widget)
        button_layout = QHBoxLayout()
        self.use_btn = QPushButton("Use")
        self.use_btn.setFixedWidth(80)
        self.use_btn.clicked.connect(self._on_use_selected)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setFixedWidth(80)
        self.delete_btn.clicked.connect(self._on_delete)
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setFixedWidth(100)
        self.clear_btn.clicked.connect(self._on_clear_all)
        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedWidth(80)
        self.close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.use_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
    def _populate_list(self):
        self.list_widget.clear()
        for pwd in self.passwords:
            masked = pwd[:4] + "••••" if len(pwd) > 4 else pwd
            self.list_widget.addItem(masked)
    def _on_use(self, item):
        row = self.list_widget.row(item)
        if 0 <= row < len(self.passwords):
            self.selected_password = self.passwords[row]
            self.accept()
    def _on_use_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self._on_use(item)
        else:
            QMessageBox.information(self, "No Selection", "Select a password from the list first.")
    def _on_delete(self):
        item = self.list_widget.currentItem()
        if item:
            row = self.list_widget.row(item)
            if 0 <= row < len(self.passwords):
                self.passwords.pop(row)
                self._populate_list()
    def _on_clear_all(self):
        reply = QMessageBox.question(
            self, "Clear All",
            "Remove all saved passwords?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.passwords = []
            self._populate_list()
