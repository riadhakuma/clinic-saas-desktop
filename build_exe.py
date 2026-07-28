import os
import shutil
import subprocess
import sys

def find_pyinstaller():
    """Finds pyinstaller executable on system or virtualenv."""
    pyi_path = shutil.which("pyinstaller")
    if pyi_path:
        return pyi_path
    
    user_scripts = r"C:\Users\attac\AppData\Local\Python\pythoncore-3.14-64\Scripts\pyinstaller.exe"
    if os.path.exists(user_scripts):
        return user_scripts
        
    return "pyinstaller"

def build():
    print("==================================================")
    print("   Building Standalone Clinic SaaS Executable     ")
    print("==================================================")
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(project_dir, "app", "static")
    separator = ";" if os.name == "nt" else ":"
    
    add_data_arg = f"{static_dir}{separator}app/static"
    pyinstaller_bin = find_pyinstaller()
    
    cmd = [
        pyinstaller_bin,
        "--name=ClinicManager",
        "--onefile",
        "--noconsole",
        f"--add-data={add_data_arg}",
        "--collect-all=uvicorn",
        "--collect-all=fastapi",
        "--collect-all=starlette",
        "--collect-all=webview",
        "--collect-all=pydantic",
        "--collect-all=anyio",
        "--hidden-import=sqlite3",
        "--hidden-import=win32timezone",
        "main_launcher.py"
    ]
    
    print("Executing Command:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=project_dir)
    
    if result.returncode == 0:
        dist_exe = os.path.join(project_dir, "dist", "ClinicManager.exe" if os.name == "nt" else "ClinicManager")
        print("\n SUCCESS!")
        print(f"Standalone .EXE generated at:\n -> {dist_exe}")
        print("\nYour clients can copy and run this single .exe on ANY Windows PC without installing Python, PIP, or any dependencies!")
    else:
        print("\n BUILD FAILED! Check error log above.")

if __name__ == '__main__':
    build()
