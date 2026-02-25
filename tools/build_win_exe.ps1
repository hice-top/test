param(
  [string]$Python = "python",
  [string]$Name = "WindowsOneClickInstaller"
)

Write-Host "[1/2] Installing pyinstaller..."
& $Python -m pip install --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/2] Building EXE..."
& $Python -m PyInstaller --noconfirm --onefile --windowed --name $Name app/gui.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Done. Output: dist/$Name.exe"
