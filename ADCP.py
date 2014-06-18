# TODO: update usage text

USAGE = """

GP- This has been modified to make it a generic raw socket connection, with <CR><LF>

This program allows direct user interaction with the TMPSF instrument via a socket.


USAGE:
    TMPSF_logged_2.py address port basename # connect to instrument on address:port, with logger basename
    TMPSF_logged_2.py address port basename # connect to instrument on address:port, with logger defaulted to generic basename
    TMPSF_logged_2.py port              # connect to instrument on localhost:port, with logger defaulted to generic basename
    
    

Example:
    TMPSF_logged_2.py 10.180.80.169 2101 TMPSF_10.180.80.169_2101
    

It establishes a TCP connection with the provided service, starts a thread to
print all incoming data from the associated socket, and goes into a loop to
dispatch commands from the user. In this "logged" version the script stops any sampling,
initializes a new sampling program.

Commands accepted: 
    "clear" - erases flash memory and resets sampling mode
    "sample,X" - initializes sampling with a period defined by "X" in seconds (must be less than 100)
    "q" - closes TCP connection and exits program

"""

__author__ = 'Ryan Cox'
__license__ = 'Apache 2.0'

import sys
import socket
import os
import re
import time
import select
from logger import Logger   #logger.py is in Ryan's python $path C:/python27
from threading import Thread

# Thread to receive and print data.
class _Recv(Thread):
    def __init__(self, conn, basename):
        Thread.__init__(self, name="_Recv")
        self._conn = conn
        self.myFileHandler = Logger(basename)
        print "logger initialized with basename %s, will create new file and name at 00:00UTC daily" % (basename)
        self._last_line = ''
        self._new_line = ''
        self.setDaemon(True)

    # The _update_lines method adds each new character received to the current line or saves the current line and creates a new line
    def _update_lines(self, recv):
        if recv == "\n":  #TMPSF data line terminates with a ?, most I/O is with a '\n'
            self._new_line += recv #+ "\n" #this keeps the "#" in the I/O
            self._last_line = self._new_line
            self._new_line = ''
            return True
        else:
            self._new_line += recv
            return  False
            
    # The run method receives incoming chars and sends them to _update_lines, prints them to the console and sends them to the logger.
    def run(self):
        print "### _Recv running."
        while True:
            recv = self._conn.recv(1)
            newline = self._update_lines(recv)
            os.write(sys.stdout.fileno(), recv)   #this writes char by char-- use commented out 'if newline' to write as a line
            self.myFileHandler.write(recv)    #writes to logger file  

            # uncomment code below to print by lines instead of by characters.
            # if newline:
                 # os.write(sys.stdout.fileno(), self._last_line)  #writes to console
                 # myFileHandler.write( self._last_line )    #writes to logger file   + "\n"
                    
            sys.stdout.flush()

# Main program
class _Direct(object):
    # Establishes the connection and starts the receiving thread.
    def __init__(self, host, port, basename, configuration):
        print "### connecting to %s:%s" % (host, port)  
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((host, port))
        self._bt = _Recv(self._sock, basename)
        self._bt.start()
        
        # wake and connect to instrument
        self.send('+++') # wakes instrument **** can you send a string?
        time.sleep(0.5)
        
        # initialize system settings
        self.send('CR1') # 'CR1' factory default, 'CR0' user default
        time.sleep(0.5)
        
        # print status messages
        self.send('PS0') # output system configuration
        time.sleep(0.5)
        self.send('AC') # output active calibration data
        time.sleep(0.5)
        self.send('FD') # output fault log **** useful??
        time.sleep(0.5)
        self.send('PT200') # 'PT200' runs all tests.  'PT300' runs all tests continuously
        
        # Configures system settings based on specified configuration
        # TODO: confirm configuration names and settings
        if configuration == 'CONF1':
            self.send('WF0176')
            time.sleep(0.5)
            self.send('WN22')
            time.sleep(0.5)
            self.send('WS400')
            time.sleep(0.5)
        elif configuration == 'CONF2':
            self.send('WN40')
            time.sleep(0.5)
            self.send('WS400')
            time.sleep(0.5)
        elif configuration == 'CONF3':
            self.send('WN40')
            time.sleep(0.5)
            self.send('WS1600')
            time.sleep(0.5)
        elif configuration == 'CONF4':
            self.send('WF0352')
            time.sleep(0.5)
            self.send('WN50')
            time.sleep(0.5)
        elif configuration == 'CONF5':
            self.send('WF0352')
            time.sleep(0.5)
            self.send('WN30')
            time.sleep(0.5)
        elif configuration == 'CONF6':
            self.send('WN28')
            time.sleep(0.5) 
            self.send('WS3200')
            time.sleep(0.5)
        elif configuration == 'CONF7':
            self.send('WF0352')
            time.sleep(0.5)
            self.send('WN50')
            time.sleep(0.5) 
        elif configuration == 'CONF8':
            self.send('WF0352')
            time.sleep(0.5)
            self.send('WN30')
            time.sleep(0.5) 
            
        # TODO: specify user commands
        print "### Status checks complete, but not verified"
        print "### To run in water test enter 'test'"
        print "### To erase memory and reset sampling enter 'clear'"
        print "### To initialize sampling mode enter 'sample,X' where X is sample period in seconds"
        print "### To close socket and exit program enter 'q'"
    
    # Dispatches user commands.    
    def run(self):
        while True:
        
            cmd = sys.stdin.readline()
            
            cmd = cmd.strip()
            cmd1 = cmd.split(",")
            
            if cmd=="q":
                print "### exiting"
                break
            
            # TODO: add commands??
            elif cmd== "other??":
                pass # ****
                
            elif cmd== "test":
                print "start test"
                self.send('PT200')
                time.sleep(0.5)
                
            elif cmd1[0] == "sample":
                # TODO: send sampling commands
                print "sampling started"
                
            else:
                print "### sending '%s'" % cmd
                self.send(cmd)
                self.send('\r\n')

        self.stop()
    
    # closes the connection to the socket
    def stop(self):
        self._sock.close()
    
    # Sends a string. Returns the number of bytes written.
    def send(self, s):
        c = os.write(self._sock.fileno(), s)
        return c

# main method.  Accepts input parameters runs the program
# default host: 'localhost'
# default port: no default
# default basename: "INSTNAME_IPADDR_PORT"
# default configuration: CONF1
if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print USAGE
        exit()
    
    # TODO: may be possible to do this more cleanly with default values in the init function of direct
    if len(sys.argv) == 2:
        host = 'localhost'
        port = int(sys.argv[1])
        basename = "INSTNAME_IPADDR_PORT"
        configuration = "CONF1"
        
    if len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
        basename = "INSTNAME_IPADDR_PORT"
        configuration = "CONF1"
        
    if len(sys.argv) == 4:
        host = sys.argv[1]
        port = int(sys.argv[2])
        basename = sys.argv[3]
        configuration = "CONF1"
        
    else:
        host = sys.argv[1]
        port = int(sys.argv[2])
        basename = sys.argv[3]
        configuration = sys.argv[4] 

    direct = _Direct(host, port, basename, configuration)
    direct.run()

