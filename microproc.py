import subprocess
import sys

maxbatches = int(sys.argv[2])
itemsperbatch = 10
permastart = int(sys.argv[1])
interval = 1

# maxbatches = int(sys.argv[2]);itemsperbatch = 10;permastart = int(sys.argv[1]);interval = 10


for i in range(1, maxbatches+1):
    
    processes = []
    start = permastart + (i-1)*interval*itemsperbatch
    end = start + interval*itemsperbatch - 1
    print(f"Batch {i}:")
    for j in range(start, end+1, interval):
        print(f"{j}-{j+interval-1}")
        
        cmd = f"python pexurls.py {j} {j+interval-1}"  # command to run the script with start and end arguments
        # print(cmd); continue
        p = subprocess.Popen(cmd, shell=True)  # create a process object for the command
        processes.append(p) 
        
    for p in processes:
        p.wait()
    print("\n"*10)
print(" ".join(sys.argv))