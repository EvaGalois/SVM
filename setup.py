from cx_Freeze import setup, Executable
import sys

# 依赖项设置: 如果你的脚本依赖于其他Python库，请在这里添加
build_exe_options = {
    "packages": ["tkinter", "requests", "json", "numpy", "os", "time"],
    "excludes": ["matplotlib", "scipy"],  # 排除一些你不需要的大型库
    "include_files": ["aggregated_data.json"],  # 如果有其他文件需要包含进去，比如数据库文件、配置文件等
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="模仁推荐机",
    version="1.0",
    description="模仁推荐应用程序",
    options={"build_exe": build_exe_options},
    executables=[Executable("cpk.py", base=base, target_name="模仁推荐机.exe", icon="app_icon.ico")],  # 可以指定一个图标文件路径
)
