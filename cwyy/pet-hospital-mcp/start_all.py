import subprocess
import sys
import time
import os

# Start pethospital.exe
print("Starting pethospital.exe...")
subprocess.Popen(
    [r"C:\Users\拾捌\Desktop\pet-hospital-windows-amd64\windows\pethospital.exe"],
    cwd=r"C:\Users\拾捌\Desktop\pet-hospital-windows-amd64\windows",
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)
time.sleep(2)
print("pethospital.exe started.")

# Start MCP server
print("Starting MCP server...")
os.chdir(r"C:\Users\拾捌\Desktop\pet-hospital-windows-amd64\windows\pet-hospital-mcp")
subprocess.run([sys.executable, "main.py"], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
