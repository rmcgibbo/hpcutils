#!/usr/bin/env python

import os,sys,socket

# This is meant to be a standalone script.

class Cluster:
    def __init__(self):
        #####################################################
        ### Names of commands sent to the queueing system ###
        #####################################################
        self.qstat_command = 'qstat -f -1'
        self.nodes_command = 'pbsnodes'
        self.diagnose_priorities = 'diagnose -p'
        self.diagnose_errors = 'diagnose -q'
        self.checknode_command = 'checknode '
        ############################################################
        ###  Attributes of the cluster that we're interested in  ###
        ###               We initialize them here                ###
        ############################################################
        self.Jobs = {}            # All the jobs running on the cluster
        self.Nodes = []           # All of the nodes on the cluster
        self.priorities = {}      # Priorities of queued jobs
        self.job_errors = {}      # Jobs not running due to error
        self.user_slots = {}      # Number of slots taken by user
        self.groups     = {}      # Names of research groups (useful only on large clusters)
        #####################################################
        ###  Subroutines to be run when class is started  ###
        #####################################################
        self.MakeJobList()        # Creates self.Jobs
        self.MakeNodeList()       # Makes the list of nodes
        self.GetUserSlots()       # Summarizes number of slots taken by user
        self.DiagnosePriorities() # Gathers priorities for queued jobs
        self.GetJobErrors()       # Gathers errors for jobs that aren't running
        
    def MakeJobList(self):
        # Build a list of jobs.
        cjob = None
        for line in os.popen(self.qstat_command):
            if len(line.split()) == 0:
                continue
            elif line[:7] == "Job Id:":
                if cjob != None:
                    self.Jobs[cjob.Number] = cjob
                # Initialize the new class
                cjob = Job()
                cjob.Number = int(line.split()[-1].split('.')[0])
            elif line.split()[0] == "Job_Owner":
                cjob.User = line.split()[-1].split('@')[0]
            elif line.split()[0] == "Job_Name":
                cjob.Name = line.split()[-1]
            elif line.split()[0] == "queue":
                cjob.Queue = line.split()[-1]
            elif line.split()[0] == "exec_host":
                exec_hosts = [i.split('/')[0] for i in line.split()[-1].split('+')]
                if "certainty" in socket.gethostname():
                    cjob.Processors = len(set(exec_hosts)) * 24
                else:
                    cjob.Processors = len(exec_hosts)
            elif line.split()[0] == "Resource_List.nodect":
                # The "job-exclusive" and "free" states are not informative
                cjob.NodeCt = int(line.split()[-1])
            elif line.split()[0] == "job_state":
                # Job is queued
                if line.split()[-1] == "Q":
                    cjob.Status = "Q"
                # Job is running
                elif line.split()[-1] == "R":
                    cjob.Status = "R"
                # Job is on hold
                elif line.split()[-1] == "H":
                    cjob.Status = "H"
                # Job is in error state
                elif line.split()[-1] == "E":
                    cjob.Status = "E"
                else:
                    print "I don't know what to do with this:"
                    print line,
        self.Jobs[cjob.Number] = cjob

    def MakeNodeList(self):
        # Build a list of nodes.
        cnode = None
        for line in os.popen(self.nodes_command):
            if len(line.split()) == 0:
                continue
            # I recognize that the line corresponds to a node name if 
            elif len(line.split()) == 1 and line[0] != " ":
                if cnode != None:
                    self.Nodes.append(cnode)
                # Initialize the new class
                cnode = Node()
                cnode.Queues = []
                cnode.Name = line.strip()
                cnode.JobNumbers = set([])
            elif line.split()[0] == "np":
                cnode.Num_Procs = int(line.split()[-1])
            elif line.split()[0] == "jobs":
                cnode.JobNumbers = set([int(i.split("/")[-1].split('.')[0]) for i in line.split("=")[-1].split(",")])
                cnode.Num_Running = len(line.split()) - 2
            elif line.split()[0] == "status":
                # The mighty genexp
                # Splits the line by commas, and for each chunk, check if the field before equals sign is "loadave".
                # If so, set Load equal to the field after equals sign.
                cnode.Load = float((i.split('=')[1] for i in line.split(',') if i.split('=')[0] == 'loadave').next())
            elif line.split()[0] == "state":
                #print cnode.State
                # The "job-exclusive" and "free" states are not informative
                cnode.State = line.split()[-1]
                #cnode.State = line.split()[-1].replace('free','').replace('job-exclusive','')
            elif line.split()[0] == "properties":
                # The "job-exclusive" and "free" states are not informative
                cnode.Queues = line.split()[-1].split(",")
        self.Nodes.append(cnode)

    def DiagnosePriorities(self):
        # List of priority values for queued jobs
        self.priorities = {}
        for line in os.popen(self.diagnose_priorities):
            if len(line.split()) < 2: continue
            try:
                self.priorities[int(line.split()[0])] = int(line.split()[1])
            # Sometimes the first word is not an integer, ignore this error.
            except ValueError: continue
            
    def GetJobErrors(self):
        # List of errors for queued jobs that don't have priorities
        self.job_errors = {}
        for line in os.popen(self.diagnose_errors):
            if len(line.split()) < 3: continue
            try:
                self.job_errors[int(line.split()[1])] = ' '.join(line.split()[2:])
            # Sometimes the first word is not an integer, ignore this error.
            except ValueError: continue
    
    def GetUserSlots(self):
        # From the jobs-dictionary, figure out which users are using how many slots
        self.user_slots = {}
        self.groups = {}
        for job_number in self.Jobs:
            job = self.Jobs[job_number]
            user = job.User
            try: # Sometimes the group file isn't readable
                group = os.popen('grep %s /etc/group' % user).readlines()[0].split(':')[0]
            except:
                group = "NoGroup"
            np   = job.Processors
            self.groups[user] = group
            if user not in self.user_slots:
                self.user_slots[user] = np
            else:
                self.user_slots[user] += np

    def PrintUserGroupSummary(self):
        Total = 0
        print
        print "%22s : %-5s" % ('User','Slots')
        print "------- START -------"
        for user in sorted([i for i in self.user_slots]):
            usergroup = "%s (%s)" % (user,self.groups[user])
            print "%22s : %5i" % (usergroup,self.user_slots[user])
            Total += self.user_slots[user]
        print "-------- END --------"
        print "%22s : %5i" % ('Total',Total)

    def PrintUserSummary(self):
        Total = 0
        print
        print "%12s : %-5s" % ('User','Slots')
        print "------- START -------"
        for user in sorted([i for i in self.user_slots]):
            print "%12s : %5i" % (user,self.user_slots[user])
            Total += self.user_slots[user]
        print "-------- END --------"
        print "%12s : %5i" % ('Total',Total)

    def PrintGroupSummary(self):
        group_slots = {}
        for user in sorted([i for i in self.user_slots]):
            group = self.groups[user]
            if group not in group_slots:
                group_slots[group] = self.user_slots[user]
            else:
                group_slots[group] += self.user_slots[user]
        Total = 0
        print
        print "%12s : %-5s" % ('Group','Slots')
        print "------- START -------"
        for group in sorted([i for i in group_slots]):
            print "%12s : %5i" % (group,group_slots[group])
            Total += group_slots[group]
        print "-------- END --------"
        print "%12s : %5i" % ('Total',Total)

    def PrintRunningJobs(self):
        print
        print "Info for Running Jobs"
        print "%-10s %25s %10s %10s %10s %5s" % ('Job Number','Job Name','User','Group','Queue','Slots')
        print "---------------------------------- START ----------------------------------"
        for job_number in sorted([j for j in self.Jobs]):
            job = self.Jobs[job_number]
            print "%-10i %25s %10s %10s %10s %5i" % (job.Number, job.Name[:25], job.User, self.groups[job.User], job.Queue, job.NodeCt*24)
        print "----------------------------------- END -----------------------------------"
        print

    def PrintQueuedJobs(self):
        good_jobs = {}
        bad_jobs = {}
        #self.priorities = []
        for job_number in self.Jobs:
            job =self.Jobs[job_number]
            #print job.Name, job.Status
            if job.Status in "QH":
                message, state = self.GetStatusofQueuedJob(job_number)
                if state == 0:
                    good_jobs[job.Number] = "%-10i %25s %10s %10s %10s %5i : Priority = % i" % (job.Number, job.Name[:25], job.User,  self.groups[job.User], job.Queue, job.NodeCt*24, message)
                    #self.priorities.append([job.Number,message])
                elif state == 1:
                    bad_jobs[job.Number] = "%-10i %25s %10s %10s %10s %5i : %s" % (job.Number, job.Name[:25], job.User,  self.groups[job.User], job.Queue, job.NodeCt*24, message)
        print "Info for Queued Jobs"
        print "%-10s %25s %10s %10s %10s %5s : Message" % ('Job Number','Job Name','User','Group','Queue','Slots')
        print "----------------------------------  GOOD ----------------------------------"
        # This complicated-looking line prints out the queued jobs in order of decreasing priority.
        for i in self.argsort([self.priorities[j] for j in self.priorities])[::-1]:
            k = [j for j in self.priorities][i]
            print good_jobs[k]
        print "----------------------------------- BAD -----------------------------------"
        for i in sorted([j for j in bad_jobs]):
            print bad_jobs[i]
        print "----------------------------------- END -----------------------------------"

    def PrintNodeSummary(self,free=False):
        line_count = 0
        print "Info for Nodes"
        for node in self.Nodes:
            Prefix=""
            c = node.Num_Procs
            u = node.Num_Running
            if free:
                # Skip over nodes that are offline, down, or have >=1 slots used.
                if u >= 1 or "offline" in node.State or "down" in node.State:
                    continue
            if line_count % 48 == 0:
                print "-------------------------------------------------------------------------------------------------------"
                print "%-15s :  Tot/Use   ( Load) %40s %15s" % ("Name","User:Job(Queue)[Number]","State")
                print "-------------------------------------------------------------------------------------------------------"
            JobString = ','.join(["%s:%s(%s)[%i]" % (self.Jobs[i].User,self.Jobs[i].Name[:10],self.Jobs[i].Queue,self.Jobs[i].Number) for i in node.JobNumbers])
            if len(JobString) == 0 and 'down' not in node.State and 'offline' not in node.State:
                Prefix="\x1b[92m"
                JobString = "Free! (Properties: %s)" % ",".join(node.Queues)
            #QueueString = ','.join([Jobs[i].Queue for i in node.JobNumbers])
            #print len(JobString)
            #print "%40s" % JobString, len(JobString)
            print "%-15s :   %2i/%2i    (%5.2f) %s%40s\x1b[0m %15s" % (node.Name[:15], c, u, node.Load, Prefix, JobString, node.State)
            line_count += 1
            
    def argsort(self,seq):
        # http://stackoverflow.com/questions/3071415/efficient-method-to-calculate-the-rank-vector-of-a-list-in-python
        return sorted(range(len(seq)), key=seq.__getitem__)

    def GetStatusofQueuedJob(self,Number):
        # The priority of a queued job is not immediately obvious from qstat.
        # On certainty you need to run diagnose -p
        try:
            return self.priorities[Number], 0
        except:
            return self.job_errors[Number], 1


class Job:
    def __init__(self):
        self.Number = 0
        self.Name = 'NoName'
        self.User = 'Nobody'
        self.Processors = 0
        self.Priority = None
        self.Queue = 'NoQueue'
        self.Status = 'NoStatus'
        self.NodeCt = 1

class Node:
    def __init__(self):
        self.Name = 'NoName'
        self.State = 'NoState'
        self.Load = 0.0
        self.Num_Procs = 0
        self.Num_Running = 0
            
def main():
    print """Usage: PBSCheck.py options
    where options is one or more of: \x1b[1muser, group, running, queued, nodes, freenodes\x1b[0m
    
    What it does:
    user, group will return the total number of nodes being used by individual users or groups
    running will return a list of running jobs
    queued will return a list of queued/halted jobs, including priorities/reasons
    nodes will return a list of compute nodes, the number of used slots, load, and jobs that are running on it
    freenodes will return a list of compute nodes that are not down or offline and have free slots
    """

    C = Cluster()

    if "user" in sys.argv:
        C.PrintUserSummary()
    if "group" in sys.argv:
        C.PrintGroupSummary()
    if "running" in sys.argv:
        C.PrintRunningJobs()
    if "queued" in sys.argv:
        C.PrintQueuedJobs()
    if "nodes" in sys.argv:
        C.PrintNodeSummary()
    if "freenodes" in sys.argv:
        C.PrintNodeSummary(free=True)

if __name__ == "__main__":
    main()
