@echo off
REM 优先使用已装好 PySide6 / PyInstaller 的系统 Python 3.13
REM （仅在本脚本会话内生效，不改全局 PATH，避免影响其他程序）
set "PATH=C:\Programs\Python\Python313;C:\Programs\Python\Python313\Scripts;%PATH%"
REM ==========================================
REM Wallpace — PyInstaller 打包脚本
REM 用法: 双击运行或在 cmd 中执行
REM ==========================================
REM 确保工作目录切换为脚本所在目录（双击运行时也能正确打包）
cd /d "%~dp0"

echo [1/3] 检查 Python 环境...
python --version || (
  echo 错误: 未找到 Python，请先安装 Python 3.10+
  pause
  exit /b 1
)

echo [2/3] 安装依赖（含 PyInstaller）...
pip install -r requirements.txt || (
  echo 错误: 依赖安装失败
  pause
  exit /b 1
)

echo.
echo 检查 PyInstaller...
pyinstaller --version >nul 2>&1 || (
  echo PyInstaller 未安装，正在安装...
  pip install pyinstaller
)
pyinstaller --version >nul 2>&1 || (
  echo 错误: PyInstaller 安装失败，无法继续打包
  pause
  exit /b 1
)

echo [3/3] 使用 PyInstaller 打包...
pyinstaller ^
  --name wallpace ^
  --windowed ^
  --onefile ^
  --clean ^
  src/main.py

echo.
if exist "dist\wallpace.exe" (
  echo ==========================================
  echo 打包完成！可执行文件位于: dist\wallpace.exe
  echo ==========================================
) else (
  echo 错误: 打包失败，请检查上方日志
)
pause