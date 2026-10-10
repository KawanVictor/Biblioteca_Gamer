@echo off
rem Gera dist\BibliotecaGamer.exe. Rode na raiz do projeto, com o ambiente virtual ativado.
rem O .exe guarda banco, capas e backups em %APPDATA%\BibliotecaGamer.
python -m pip install --quiet pyinstaller || exit /b 1
python -m PyInstaller --noconfirm --clean --onefile --windowed --name BibliotecaGamer ^
    --icon assets\icone.ico --add-data "assets\icone.ico;assets" main.py || exit /b 1
echo.
echo Pronto: dist\BibliotecaGamer.exe
