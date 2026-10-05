 $ErrorActionPreference = "Continue"
 $out = @()
 $out += "=== STEGANO EVIDENCE PACKAGE ==="
 $out += "=== Generated: $(Get-Date) ==="
 $out += ""
 $out += "=== LEDGER ==="
 $out += git log --oneline
 $out += ""
 $out += "=== FUNCTION MAP: Stegano.py ==="
 $out += Select-String -Path Stegano.py -Pattern "^\s*(def |class )"
 $out += ""
 $out += "=== Stegano.py: lines 1-400 ==="
 $out += Get-Content Stegano.py | Select-Object -First 400
 $out += ""
 $out += "=== Stegano.py: lines 401-800 ==="
 $out += Get-Content Stegano.py | Select-Object -Skip 400 -First 400
 $out += ""
 $out += "=== Stegano.py: lines 801-1200 ==="
 $out += Get-Content Stegano.py | Select-Object -Skip 800 -First 400
 $out += ""
 $out += "=== Stegano.py: lines 1201-end ==="
 $out += Get-Content Stegano.py | Select-Object -Skip 1200
 $out += ""
 $out += "=== steganography_utils.py (complete) ==="
 $out += Get-Content steganography_utils.py
 $out += ""
 $out += "=== password_utils.py (complete) ==="
 $out += Get-Content password_utils.py
 $out += ""
 $out += "=== workers.py (complete) ==="
 $out += Get-Content workers.py
 $out += ""
 $out += "=== ui_components.py (complete) ==="
 $out += Get-Content ui_components.py
 $out += ""
 $out += "=== audio_manager.py (complete) ==="
 $out += Get-Content audio_manager.py
 $out += ""
 $out += "=== SESSION_NOTES.md (complete) ==="
 $out += Get-Content SESSION_NOTES.md
 $out += ""
 $out += "=== END OF PACKAGE ==="
 $out | Set-Content evidence_package.txt -Encoding UTF8
Write-Host "PACKAGE CREATED: evidence_package.txt"
Write-Host "Size: $((Get-Item evidence_package.txt).Length) bytes"
