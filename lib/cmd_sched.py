'''
Execute a list of commands, num_concurrent
at a time. This is useful if each command
uses one processor and you want all of your
processors concurrently.
'''

import subprocess
import time
def cmd_sched(cmds, num_concurrent):
    '''Execute each command in the list of commands
    cmds, num_concurrent at a time'''
    current = []
    while len(cmds) > 0:
        while len(current) < num_concurrent and len(cmds) > 0:
            cmd = cmds.pop()
            sp = subprocess.Popen(cmd, bufsize=-1, shell=True)
            current.append((cmd,sp))

        # sleep 0.1 s
        time.sleep(0.1)
        finished = []
        for cmd, sp in current:
            sp.poll()
            if sp.returncode != None:
                if sp.returncode < 0:
                    print >> sys.stderr, '%s returned %s' % (cmd, sp.returncode)
                finished.append((cmd,sp))

        for cmd,sp in finished:
            current.remove((cmd,sp))
        
    return None

if __name__ == '__main__':
    cmd_sched(['echo hello; sleep 1'  for i in range(5)], 2)
