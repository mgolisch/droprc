'''
Created on 14.12.2012

@author: mgolisch
'''
import time
import threading
import os
import sys
import json
import atexit
import signal
import readline
from colorama import init
init(autoreset=True)

homedir = os.path.expanduser("~")
basedir = homedir + "/Dropbox/droprc/"
socketdir = basedir + "/sockets/"
commandfile = socketdir + "command"
commandlistfile = socketdir + "commandlist.json"
outputfile = socketdir + "output"
statusfile = socketdir + "status"
curdirfile = socketdir + "curdir"

thismodule = sys.modules[__name__]
exit_client = False

def signal_handler(signal, frame):
        print 'You pressed Ctrl+C!'
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

@atexit.register
def cleanup():
    if os.path.exists(outputfile): os.remove(outputfile)

def exitclient():
    print "exiting client"
    global exit_client
    exit_client = True


def run_command():
    commandline = str(raw_input("--> "))
    if commandline == "exit" :
        exitclient()
        return
    print 'running command ' + commandline
    print
    with open(commandfile,'w') as command:
        command.write(commandline)
        command.close()
    read_output()

def read_status():
    with open(statusfile) as status:
        print "remote server running"
        for line in status.readlines():
            print line.replace("\n","")
        print

def noresponse():
    print "\r\ngot no response from server within 60 seconds"
    print "the server probably crashed"
    exitclient()

def read_output():
    print "waiting for server response"
    timer = threading.Timer(60.0,noresponse)
    timer.start()
    wait_cursor = "."
    while not os.path.exists(outputfile):
        if exit_client : return
        sys.stdout.write("\r"+wait_cursor)
        sys.stdout.flush()
        wait_cursor = wait_cursor+"."
        time.sleep(1)
    timer.cancel()   
    print "\r\ngot respone after "  +str(len(wait_cursor)) + " seconds"
    with open(outputfile) as output:
        for line in output.readlines():
            print line.replace("\n","")
    os.remove(outputfile)

#start
print "dropbox remotecontrol client v.0.1 by mgolisch <mgolisch@googlemail.com>"
if not os.path.exists(statusfile):
    print "error: server not running on remote machine\n"
    sys.exit(1)

read_status()         
while not exit_client:
    if not os.path.exists(statusfile):
        print "error: server not running anymore on remote machine\n"
        exit_client = True
        continue
    run_command()
