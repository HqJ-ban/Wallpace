@echo off
REM ==========================================
REM Wallpace — PyInstaller 打包脚本
REM 用法: 双击运行或在 cmd 中执行
REM ==========================================

echo [1/3] 检查 Python 环境...
python --version || (
  echo 错误: 未找到 Python，请先安装 Python 3.10+
  pause
  exit /b 1
)

echo [2/3] 安装依赖...
pip install -r requirements.txt

echo [3/3] 使用 PyInstaller 打包...
pyinstaller ^
  --name wallpace ^
  --windowed ^
  --onefile ^
  src/main.py

echo.
echo ==========================================
echo 打包完成！可执行文件位于: dist\wallpace.exe
echo ==========================================
pause
