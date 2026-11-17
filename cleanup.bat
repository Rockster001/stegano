@echo off
rem ============================================================
rem  Stegano - one-time release cleanup
rem  - MOVES dev/test images to C:\Dev\SteganoTest (nothing is lost)
rem  - DELETES old fix scripts and backups (they remain in git history,
rem    recoverable forever with:  git checkout <commit> -- <filename>)
rem  Run this ONCE, then run save.bat to record it.
rem ============================================================
cd /d "%~dp0"
echo.
echo This will tidy the project folder for release:
echo  - test images in "Images" move to C:\Dev\SteganoTest\Images
echo  - old fix_*.py scripts, *_broken_backup.py files, text chunks,
echo    evidence files and .bak files are deleted (git keeps copies)
echo  - "Images\Virgin Images" and all program files are NOT touched
echo.
pause

rem ---- move dev/test images out of the repo ----
if not exist "C:\Dev\SteganoTest\Images" mkdir "C:\Dev\SteganoTest\Images"
for %%f in ("Images\*.png" "Images\*.jpg") do move "%%f" "C:\Dev\SteganoTest\Images\" >nul 2>&1
move "Hotpoint.png" "C:\Dev\SteganoTest\Images\" >nul 2>&1
move "audio\music\idle2.mp3" "C:\Dev\SteganoTest\" >nul 2>&1

rem ---- delete dev-only files (recoverable from git history) ----
del /q fix_diag.py fix_carry_diag.py fix_h1.py fix_highlight.py fix_highlight2.py fix_highlight3.py fix_load_diag.py fix_switch.py fix_switch2.py fix_tag.py fix_enter.py stegano_repair.py 2>nul
del /q Stegano_broken_backup.py Stegano_prerepair_backup.py steganography_utils_broken_backup.py workers_broken_backup.py 2>nul
del /q steg_part_00_lines_1-800.txt steg_part_01_lines_801-1516.txt 2>nul
del /q evidence_package.txt delta.txt collect_evidence.ps1 Stegano.bat.bak 2>nul

echo.
echo Cleanup finished. Files moved: C:\Dev\SteganoTest\Images
echo.
echo Now double-click save.bat to record this in git.
echo.
pause
