#!/usr/bin/env python
import sys, os
import threading
import time
import signal
from datetime import datetime
from fsevents import Observer, Stream
from subprocess import check_output as qx

# timestamp function (returns string like "Sat Feb  4 22:46:21 2012")
timestamp = lambda: datetime.today().strftime("%c")

#ignore actions on files whos path involves any of these strings
IGNORE = ['.git', '.svn']

# global name for threads
#OBSERVER = None
#STREAM = None

def commit_change(event):
    '''Callback on FSEvent. Commit to local git'''
    
    # ignore anything that goes in in a .git or .svn folder
    if any([ig in event.name for ig in IGNORE]):
        return
        
    if event.mask == 256 or event.mask == 128: # new file
        msg = 'Registered: %s' % event.name
        qx(['git', 'add', event.name])
        
        message = '"%s [%s]"' % (msg, timestamp())
        print qx(['git', 'commit', '-m', message])
        
    elif event.mask == 64 or event.mask == 512: # 64 is from mv, 512 from rm
        msg = 'Deleted: %s' % event.name
        message = '"%s [%s]"' % (msg, timestamp())
        os.system('git rm %s' % event.name)
        os.system('git commit -a -m %s' % message)
        #print qx(['git', 'commit', '-m', message])
        
    elif event.mask == 2: # from change
        msg = 'Changed: %s' % event.name
        qx(['git', 'add', event.name])
        
        message = '"%s [%s]"' % (msg, timestamp())
        print qx(['git', 'commit', '-m', message])
    else:
        raise ValueError("I cant deal with this event: %s" % event)
    


class Pusher(threading.Thread):
    """Thread that wakes up and pushed git repo"""
    
    def __init__(self, interval=60):
        threading.Thread.__init__(self)
        self.interval = interval
        self.daemon = True

    def run(self):
        while True:
            if self.have_changes():
                self.push()
            else:
                print "[Pusher] No changes"
            time.sleep(self.interval)
        
    def push(self):
        print "Pushing local repo [%s]" % timestamp()
        qx(['git', 'push'])
        
    def have_changes(self):
        output = qx(['git', 'status'])
        if "Your branch is ahead of" in output:
            return True
        return False
        
def sigint_handler(signum, frame):
    "handler for signit that kills the FSEvent thread"
    global STREAM, OBSERVER
    OBSERVER.unschedule(STREAM)
    OBSERVER.stop()
    sys.exit()

def main():
    global STREAM, OBSERVER, PUSHER
    
    try:
        working_dir = sys.argv[1]
    except:
        print >> sys.stderr, "Usage %s: directory" % sys.argv[0]
        sys.exit(1)
    abspath =  os.path.abspath(working_dir)
    os.chdir(abspath)
    
    # register signal handler
    signal.signal(signal.SIGINT, sigint_handler)
    
    # initialize the FS event thread
    OBSERVER = Observer()
    OBSERVER.start()
    STREAM = Stream(commit_change, abspath, file_events=True)
    OBSERVER.schedule(STREAM)
    print "Monitoring..."
    
    # initialize the pusher
    pusher = Pusher(interval=60*60) #push interval of 1 hour
    pusher.start()
    
    # for some reason this seems necessary to get the signal handling
    # to work
    while True:
        time.sleep(10000000)
if __name__ == '__main__':
    main()





