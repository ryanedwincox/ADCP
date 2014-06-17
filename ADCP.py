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

# create an output logger file handler
# myFileHandler = Logger("TMPSF_10.180.80.169_2101_")  #worked here, now moved to _Recv, with basename passed from command line to _Direct to _Recv

class _Recv(Thread):
    """
    Thread to receive and print data.
    """

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


class _Direct(object):
    """
    Main program.
    """

    def __init__(self, host, port, basename):
        """
        Establishes the connection and starts the receiving thread.
        """
        print "### connecting to %s:%s" % (host, port)  
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((host, port))
        self._bt = _Recv(self._sock, basename)
        self._bt.start()
        
        # TODO: wake and connect to instrument
        # TODO: print status messages
        # TODO: reconfigure to default settings and then set custom settings
        # TODO: reconfigure based on different configurations

        
        # TODO: specify user commands
        print "### Status checks complete, but not verified"
        print "### To erase memory and reset sampling enter 'clear'"
        print "### To initialize sampling mode enter 'sample,X' where X is sample period in seconds"
        print "### To close socket and exit program enter 'q'"
        
    def run(self):
        """
        Dispatches user commands.
        """
        while True:
        
            cmd = sys.stdin.readline()
            
            cmd = cmd.strip()
            cmd1 = cmd.split(",")
            
            if cmd=="q":
                print "### exiting"
                break
            
            # TODO: add commands as needed
            elif cmd== "other":
                
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
# TODO: add configuration parameter
if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print USAGE
        exit()

    if len(sys.argv) == 2:
        host = 'localhost'
        port = int(sys.argv[1])
        basename = "INSTNAME_IPADDR_PORT"
        
    if len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
        basename = "INSTNAME_IPADDR_PORT"
        
    else:
        host = sys.argv[1]
        port = int(sys.argv[2])
        basename = sys.argv[3]

    direct = _Direct(host, port, basename)
    direct.run()

