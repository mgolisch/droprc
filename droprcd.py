import time
import os
import sys
import json
import atexit
import platform
import shutil
import signal
from colorama import Fore, Back, Style

homedir = os.path.expanduser("~")
basedir = homedir + "/Dropbox/droprc/"
socketdir = basedir + "/sockets/"
xferdir = basedir + "xfer/"
commandfile = socketdir + "command"
commandlistfile = socketdir + "commandlist.json"
outputfile = socketdir + "output"
statusfile = socketdir + "status"
curdirfile = socketdir + "curdir"
hostsfile = socketdir + "hosts.json"
curhostfile = socketdir + "curhost"
thismodule = sys.modules[__name__]
commands = {}

def signal_handler(signal, frame):
        print 'You pressed Ctrl+C!'
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def write_curhost(host):
    with open(curhostfile,"w") as curhost:
        curhost.write(host)

def read_curhost():
    if not os.path.exists(curhostfile): return None
    with open(curhostfile,'r') as curhost:
        host = curhost.readline()
        curhost.close()
        return host

def write_hosts(hostlist):
    with open(hostsfile,"w") as hosts:
        hosts.write(json.dumps(hostlist))

def read_hosts():
    if not os.path.exists(hostsfile):return {}
    with open(hostsfile,"r") as hosts:
        return json.loads(hosts.read())
        
def update_status():
    with open(statusfile,'w') as status:
        hostname = platform.node()
        python_impl = platform.python_implementation()
        os_platform = platform.platform()
        status.write("your host is : " + hostname + "\n")
        status.write("running on  : " + os_platform + "\n")
        status.write("with : " + python_impl + " python version\n")
        status.write("server started :" + str(time.time())+ "\n")
        status.close()

def write_curdir(line):
    with open(curdirfile,'w') as curdir:
        curdir.writelines(line)
        curdir.close()

def read_curdir():
    if not os.path.exists(curdirfile): return '/tmp/'
    with open(curdirfile,'r') as curdir:
        directory = curdir.readline()
        curdir.close()
        return directory

def write_output(lines):
    with open(outputfile,'w') as output:
        output.writelines(lines)
        output.close()

def getcommands():
    attributes = dir(thismodule)
    commands2 = {}
    for item in attributes:
        if item.startswith("command_"):
            command_name = item.replace('command_','')
            command_func = getattr(thismodule, item)
            command_help = getattr(command_func, '__doc__')
            command_has_arg = getattr(command_func, '__has_argument__')
            command_arg_none =  getattr(command_func, '__none_argument__')
            commands[command_name] = {'command_name':command_name,'command_func':command_func,'command_help':command_help,'command_has_arg':command_has_arg,'command_none_arg':command_arg_none}
            commands2[command_name] = {'command_name':command_name,'command_help':command_help,'command_has_arg':command_has_arg,'command_none_arg':command_arg_none}
   
    with open(commandlistfile,'w') as commandlist:
        commandlist.write(json.dumps(commands2))
        commandlist.close()
    
def execute_command(command_name,argument=None):
    output = []
    command_output = []
    output.append("command was : " +Fore.BLUE+"[ " +Fore.YELLOW + command_name +Fore.BLUE + " ]"+ "\n")
    output.append("output is : " + "\n")
    if not command_name in commands.keys():
        output.append(Fore.RED + "error: command  " +Fore.BLUE+"[ " +Fore.YELLOW + command_name +Fore.BLUE + " ]"+ Fore.RED+" is not a valid command\nsee listcommands for commands" + "\n")
        write_output(output)
        return
    command_dict = commands[command_name]
    command_func = command_dict['command_func']
    command_has_arg = command_dict['command_has_arg']
    command_none_arg = command_dict['command_none_arg']
    if not command_has_arg :
        command_output = command_func()
        for item in command_output:
                output.append(item + "\n")
        write_output(output)
        return
    else:
        if not command_none_arg and argument is None:
            output.append(Fore.RED + "error: command " +Fore.BLUE+"[ " +Fore.YELLOW + command_name +Fore.BLUE + " ]"+ Fore.RED+" requires an argument but none passed" + "\n");
            write_output(output)
            return
        else:
            command_output = command_func(argument)
            for item in command_output:
                output.append(item + "\n")
            write_output(output)
            return
        
def read_command():
    if not os.path.exists(commandfile):
        return
    with open(commandfile) as command:
        command_text =    command.readline().strip()
        command_list = command_text.split(" ")
        command_name = command_list[0]
        if len(command_list) > 1:
            command_argument = command_list[1] 
        else:
            command_argument = None
        execute_command(command_name, command_argument)
        os.remove(commandfile)

@atexit.register       
def cleanup():
    if os.path.exists(commandfile): os.remove(commandfile)
    if os.path.exists(statusfile): os.remove(statusfile)
    if os.path.exists(commandlistfile): os.remove(commandlistfile)    
############
##commands##
############
    
def command_filelist(argument):
    """lists files in directory specified by argument,
     if argument is not specified it lists the content of the current directory"""
    def sort_listing(listing):
        dirs = [x for x in listing if os.path.isdir(os.path.join(argument,x)) and not x.startswith(".")]
        dirs.sort()
        dotdirs = [x for x in listing if os.path.isdir(os.path.join(argument,x)) and x.startswith(".")]
        dotdirs.sort()
        files = [x for x in listing if os.path.isfile(os.path.join(argument,x)) and not x.startswith(".")]
        files.sort()
        dotfiles = [x for x in listing if os.path.isfile(os.path.join(argument,x)) and x.startswith(".")]
        dotfiles.sort()
        dirs.extend(dotdirs)
        dirs.extend(files)
        dirs.extend(dotfiles)
        return dirs
    
    output = []
    if argument is None:
        argument = read_curdir()
    for entry in sort_listing(os.listdir(argument)):
        if os.path.isfile(argument+entry): output.append(Fore.GREEN + "[FILE] " + entry )
        if os.path.isdir(argument+entry): output.append(Fore.BLUE +  "[DIR] " +entry )
    output.insert(0, "listing of location: " + Fore.YELLOW + argument + "\n")
    return output
command_filelist.__has_argument__ = True
command_filelist.__none_argument__ = True

def command_filecd(argument):  
    """change to directory specified by argument"""
    output = []
    if os.path.exists(argument):
        if os.path.isdir(argument):
            write_curdir(argument)
            output.append("changed currentdir to : " + Fore.YELLOW + argument + "\n")
        else: output.append( Fore.RED + "error: argument  " + Fore.YELLOW + argument + Fore.RED +"is not a directory" + "\n")
    else: output.append(Fore.RED + "error: argument  " +Fore.YELLOW+ argument + Fore.RED +" does not exist" + "\n")
    return output
command_filecd.__has_argument__ = True
command_filecd.__none_argument__ = False


def command_filepwd(argument=None):  
    """returns the current directory"""
    output = []
    output.append("currentdir is : " + Fore.YELLOW + read_curdir() + "\n")
    return output
command_filepwd.__has_argument__ = False
command_filepwd.__none_argument__ = True

def command_fileget(argument=None):
    """copies the file specified by argument to the xfer directory"""
    output = []
    curdir = read_curdir()
    if not os.path.exists(curdir+argument):
        output.append(Fore.RED + "error: argument  " + Fore.YELLOW +argument + Fore.RED+" does not exist\n")
        return output
    if not os.path.isfile(curdir+argument):
        output.append(Fore.RED + "error: argument  " + Fore.YELLOW+argument + Fore.RED+" is not a file\n")
        return output
    shutil.copy(curdir+argument,xferdir)
    output.append("copied "+Fore.YELLOW+curdir+argument+Fore.RESET+" to "+Fore.YELLOW+xferdir+"\n")
    output.append("file should be syncronized by dropbox soon\n")
    return output
command_fileget.__has_argument__ = True
command_fileget.__none_argument__ = False   

def command_fileput(argument=None):
    """copies the file specified by argument from xfer dir to currentdirectory on the server"""
    output = []
    curdir = read_curdir()
    if not os.path.exists(xferdir+argument):
        output.append(Fore.RED + "error: argument  " + Fore.YELLOW +argument + Fore.RED+" does not exist\n")
        return output
    if not os.path.isfile(xferdir+argument):
        output.append(Fore.RED + "error: argument  " + Fore.YELLOW+argument + Fore.RED+" is not a file\n")
        return output
    shutil.copy(xferdir+argument,curdir)
    output.append("copied "+Fore.YELLOW+xferdir+argument+Fore.RESET+" to "+Fore.YELLOW+curdir+"\n")
    output.append("file should be syncronized by dropbox soon\n")
    return output
command_fileput.__has_argument__ = True
command_fileput.__none_argument__ = False   

def command_netping(argument=None):  
    """checks wheter a given host is up"""
    import subprocess
    output = []
    try:
        subprocess.check_call(["ping", "-c", "1", argument],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output.append("host " + Fore.YELLOW + argument + Fore.GREEN + " is UP")
    except subprocess.CalledProcessError:
        output.append("host " + Fore.YELLOW + argument + Fore.RED + " is DOWN")
   
    return output
command_netping.__has_argument__ = True
command_netping.__none_argument__ = False

def command_hostadd(argument=None):  
    """adds a host"""
    output = []
    hosts = read_hosts()
    hosts[argument] = {"name":argument,"dns":"","mac":""}
    output.append("added host : " + Fore.YELLOW + argument + "\n")
    write_hosts(hosts)
    return output
command_hostadd.__has_argument__ = True
command_hostadd.__none_argument__ = False

def command_hostremove(argument=None):  
    """removes a host"""
    output = []
    hosts = read_hosts()
    if not argument in hosts.keys():
        output.append(Fore.RED + "host not found  " + Fore.YELLOW + argument +"\n")
        return output
    hosts.pop(argument)
    output.append("removed host : " + Fore.YELLOW + argument + "\n")
    write_hosts(hosts)
    return output
command_hostremove.__has_argument__ = True
command_hostremove.__none_argument__ = False

def command_hostsethost(argument=None):  
    """sets the current host"""
    output = []
    hosts = read_hosts()
    if not argument in hosts.keys():
        output.append(Fore.RED + "host not found  " + Fore.YELLOW + argument +"\n")
        return output
    write_curhost(argument)
    output.append("set current host to : " + Fore.YELLOW + argument + "\n")
    
    return output
command_hostsethost.__has_argument__ = True
command_hostsethost.__none_argument__ = False

def command_hostgethost(argument=None):  
    """sets the current host"""
    output = []
    host = read_curhost()
    if host is None:
        output.append("no host set  \n")
        return output
    output.append("current host is : " + Fore.YELLOW + host + "\n")
    
    return output
command_hostgethost.__has_argument__ = False
command_hostgethost.__none_argument__ = False

def command_hostlist(argument=None):  
    """lists defined hosts"""
    output = []
    hosts = read_hosts()
    for key in hosts.keys():
        output.append(Fore.YELLOW + key + "\n")
    return output
command_hostlist.__has_argument__ = False
command_hostlist.__none_argument__ = False  

def command_hostsetdns(argument=None):  
    """sets dns for host"""
    output = []
    curhost = read_curhost()
    hosts = read_hosts()
    host = hosts[curhost]
    host["dns"] = argument
    hosts[curhost] = host
    write_hosts(hosts)
    output.append("set dns for host " + Fore.YELLOW + curhost + Fore.RESET + " to " + Fore.YELLOW + argument + "\n")
    return output
command_hostsetdns.__has_argument__ = True
command_hostsetdns.__none_argument__ = False  

def command_hostping(argument=None):  
    """pings a defined host using its dns attribute"""
    import subprocess
    
    output = []
    curhost = read_curhost()
    hosts = read_hosts()
    host = hosts[curhost]
    dns = host["dns"]
    if len(dns) == 0:
        output.append(Fore.RED + "error: host " + Fore.YELLOW + curhost + Fore.RED + " does not have dns attribute set\nset it using hostsetdns")
        return output
    
    try:
        subprocess.check_call(["ping", "-c", "1", dns],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output.append("host " + Fore.YELLOW + curhost + Fore.GREEN + " is UP")
    except subprocess.CalledProcessError:
        output.append("host " + Fore.YELLOW + curhost + Fore.RED + " is DOWN")
    return output
command_hostping.__has_argument__ = False
command_hostping.__none_argument__ = False

def command_hostupdatemac(argument=None):  
    """pings host, gets mac from arp and saves it in host properties (used for wol)"""
    import subprocess
    import string
    
    output = []
    curhost = read_curhost()
    hosts = read_hosts()
    host = hosts[curhost]
    dns = host["dns"]
    mac = ""
    if len(dns) == 0:
        output.append(Fore.RED + "error: host " + Fore.YELLOW + curhost + Fore.RED + " does not have dns attribute set\nset it using hostsetdns")
        return output
    
    output.append("pinging host " + Fore.YELLOW + curhost + "\n")
    try:
        subprocess.check_call(["ping", "-c", "1", dns],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output.append("host " + Fore.YELLOW + curhost + Fore.GREEN + " is UP")
    except subprocess.CalledProcessError:
        output.append("host " + Fore.YELLOW + curhost + Fore.RED + " is DOWN")
        output.append("cant get mac of offline computer\n")
        return output
    output.append("getting mac from arp cache\n")
    try:

        p =subprocess.Popen("arp -a", shell=True, stdout=subprocess.PIPE)
        arp_output, errors = p.communicate()
        if arp_output is not None :
            if sys.platform in ['linux','linux2']:
                for i in arp_output.split("\n"):
                    print i
                    if string.upper(dns) in string.upper(i):
                        for j in i.split():
                            if ":" in j:
                                mac = j
            elif sys.platform in ['win32']:
                item =  arp_output.split("\n")[-2]
                if dns in item:
                    mac = item.split()[1]
    except:
        output.append(Fore.RED + "error: something went wrong")
        return output
    if len(mac) == 0:
        output.append(Fore.RED + "error: emptymac")
        return output
    output.append("mac is " + Fore.YELLOW + mac)
    host["mac"] = mac
    hosts[curhost] = host
    write_hosts(hosts)
    return output
command_hostupdatemac.__has_argument__ = False
command_hostupdatemac.__none_argument__ = False    

def command_hostwake(argument=None):  
    """sends wol paket to  a defined host"""

    #shamelessly ripped of from http://code.activestate.com/recipes/358449-wake-on-lan/
    def wake_on_lan(macaddress):
        """ Switches on remote computers using WOL. """

        import socket
        import struct
        # Check macaddress format and try to compensate.
        if len(macaddress) == 12:
            pass
        elif len(macaddress) == 12 + 5:
            sep = macaddress[2]
            macaddress = macaddress.replace(sep, '')
        else:
            raise ValueError('Incorrect MAC address format')
 
        # Pad the synchronization stream.
        data = ''.join(['FFFFFFFFFFFF', macaddress * 20])
        send_data = '' 

        # Split up the hex values and pack.
        for i in range(0, len(data), 2):
            send_data = ''.join([send_data,
                             struct.pack('B', int(data[i: i + 2], 16))])

        # Broadcast it to the LAN.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(send_data, ('<broadcast>', 7))
    
    output = []
    curhost = read_curhost()
    hosts = read_hosts()
    host = hosts[curhost]
    mac = host["mac"]
    if len(mac) == 0:
        output.append(Fore.RED + "error: host " + Fore.YELLOW + curhost + Fore.RED + " does not have mac attribute set\nset it using hostupdatemac\n")
        return output
    
    try:
        wake_on_lan(mac)
        output.append("sent wol paket to host " + Fore.YELLOW + curhost + Fore.RESET + " with mac " + Fore.YELLOW + mac +"\n")
    except:
        output.append(Fore.RED + "error sending wol paket to host " + Fore.YELLOW + curhost + "\n")
    return output
command_hostwake.__has_argument__ = False
command_hostwake.__none_argument__ = False

print "dropbox remotecontrol server v.0.1 by mgolisch <mgolisch@googlemail.com>"
cleanup()
update_status()
getcommands()
while True:
    read_command()
    time.sleep(2)
    
    
