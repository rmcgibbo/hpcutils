import sys
import os
import re
import json
import time
import subprocess

class Qdata:
    # The total number of nodes your cluster has
    NUM_NODES = 550

    def __init__(self):
        line_format = re.compile(
            '''^                     # start at beginning of string
               (?P<JOB_ID>\d+)       # numbers (the job id)
               (.+)                  # the server name, right after the job id
               \s+
               (?P<USER>\w+)         # the user name
               \s+
               (?P<QUEUE>\w+)        # the queue name
               \s+
               (?P<NDS>[-\d]+)          # the number of nodes being used
               \s+                                                                                                                                                                    
               (?P<PROCS>[-\d]+)        # the number of processors being used. Called TSK in the table, but its really this
               \s+
               (?P<MEM>[\w-]+)       # required memory (nobody uses this anyways)
               \s+                                                                                                                                                                    
               (?P<REQ_TIME>([-]+|\d+:?\d*)) # Requested time
               \s+
               (?P<STATUS>[HRQE])     #Status. I believe this can only be H (hold) R (Running) Q (Queued) E (Error) ... What else?
               \s+                                                                                                                                                                    
               (?P<ELAP_TIME>([-]+|\d+:?\d*)) # elapsed time
               ''', #% (self.SERVER),
            re.VERBOSE)

        self.jobs = []
        qstat = subprocess.check_output('qstat -R', shell=True).split('\n')
        for line in qstat:
            m = line_format.search(line)
            if m:
                try:
                    nds = int(m.group('NDS'))
                    procs = int(m.group('PROCS'))
                except:
                    nds = 1
                    procs = 1


                self.jobs.append({'JOB_ID':    m.group('JOB_ID'),
                                  'USER':      m.group('USER'),
                                  'QUEUE':     m.group('QUEUE'),
                                  'NDS':       nds,
                                  'PROCS':     procs,
                                  'MEM':       m.group('MEM'),
                                  'REQ_TIME':  m.group('REQ_TIME'),
                                  'STATUS':    m.group('STATUS'),
                                  'ELAP_TIME': m.group('ELAP_TIME')
                                  })
            else:
                if re.search('^\d+', line):
                    print >> sys.stderr, 'A line may have been misparsed'
                    print >> sys.stderr, line

    def top_users(self, num):
        '''Return the top *num* users, and the percentage of the total number of nodes
           they're currently using
        '''

        users_by_nds = {}
        for job in self.jobs:
            # only look at currently running jobs
            if job['STATUS'] not in ['E', 'R']:
                continue

            user = job['USER']
            if user in users_by_nds:
                users_by_nds[user] += job['NDS']
            else:
                users_by_nds[user] = job['NDS']
        

        # sort by values, then reverse, then take first *num*
        top_users = (sorted(users_by_nds.iteritems(), key = lambda (k,v): (v,k)))[::-1][0:num]
        # turn it back into a list of dicts to return
        return [{'name': user, 'nds': nds} for (user, nds) in top_users]

    def fract_free(self):
        ''' Return the fraction of the nodes in the cluster that are free.
            Note: only jobs with status 'R' (Running) are counted towards the
            number of nodes in use
        '''

        nds_in_use = 0
        for job in self.jobs:
            if job['STATUS'] not in ['R']:
                continue
            nds_in_use += job['NDS']

        value = 1.0 - (nds_in_use / float(self.NUM_NODES))
        return '%.4f' % value

    def by_user(self, user):
        '''Get all the jobs owned by user /user/'''
        
        return [job for job in self.jobs if job['USER'] == user]

if __name__ == '__main__':
    q = Qdata()
    j = json.dumps({'top_users': q.top_users(num=10),
                    'fract_free':  q.fract_free(),
                    'time': time.time()
                })
    print j
    
    print q.by_user('rmcgibbo')
