#!/usr/bin/python
import subprocess
import sys
import os

with open("requirements.txt") as file:
    requirements=[line.rstrip('\n') for line in file]
        
reqs=subprocess.check_output([sys.executable,'-m','pip','freeze'])
installed_packages=[r.decode().split('==')[0] for r in reqs.split()]

missing=list()

for r in requirements:
    print(f"checking for {r}",end=' ')
    if(r in installed_packages):
        print("[OK]")
    else:
        print("[X]")
        missing.append(r)

if missing:
    answer=input("do you want to install missing packages?[Y/n] ")
    if(str.lower(answer)=="y"):
        
        cmd="pip install "+" ".join(missing)+" --user"
        print("please wait ...")
        os.system(cmd)
    
    else:
        sys.exit(1)

answer=input("do you want copy script into ~/.local/bin?[Y/n] ")

if(str.lower(answer)=="y"):
    os.system("cp ./adp.py ~/.local/bin/&& chmod +x ~/.local/bin/adp.py")
    print("done")

print("feel free and enjoy it ;)")