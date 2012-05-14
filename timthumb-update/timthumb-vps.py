#!/usr/bin/python
# This tool is to find any version of timthumb older than 
# 2.8 (The one vulnerable to remote file injection)
# This is to be ran on any host that has it's own dedicated 
# /var/www/ is the starting point but can be modified for 
# your own purposes. This can be modified by anyone for any purpose
# they see fit for their needs
import os, sys, re, urllib, shutil
from stat import *
import fileinput
import getopt
version = 0.2 
def walktree(top, log, debug):
    for f in os.listdir(top):
        if debug:
            print 'Working with %s' % f
        pathname = os.path.join(top, f)
        mode = os.lstat(pathname).st_mode
        # Don't following symlinks
        if not S_ISLNK(mode):
            # Recurse into directories
            if os.path.isdir(pathname):
                walktree(pathname, log, debug)
            # Get info on files
            elif os.path.isfile(pathname):
                regex = re.compile('thumb.php$')
                if ( re.search(regex, pathname) ):
                    if debug:
                        print "Found %s\n" % pathname
                    for line in open(pathname):
                        itsit = 0
                        foundver = 0
                        # If it's actually the timthumb script set a flag saying we've found it
                        if "TimThumb" in line:
                            itsit = 1
                        # Analyze version and break once we've done so
                        if "VERSION" in line:
                            match = re.search('(?<=VERSION....)\d\.\d+', line)
                            if match:
                                version = match.group(0)
                                print 'Version is %s\n' % version
                                if float(version) < 2.8:
                                    if debug:
                                        print "Found older timthumb\n"
                                    logfile = open(log, 'a')
                                    logfile.write(pathname)
                                    logfile.write(' version ')
                                    logfile.write(version)
                                    logfile.write('\n')
                                    replace_timthumb(pathname, log, debug)
                                else:
                                    if debug:
                                        print 'Newer than we need' 
                                break
                            foundver = 1
                    # In the event that we've found it and it didn't have a version, report it
                    # This even occurs when the version is so old it didn't store it. 
                    if itsit and not foundver:
                           logfile = open(log, 'a')
                           logfile.write(pathname)
                           logfile.write(' ')
                           logfile.write('0\n')
                           print "It's it, but doesn't have a version"
                           itsit = 0
                           foundver = 0                 
            else:
                # Unknown file type, print a message
                print 'Skipping %s' % pathname


def replace_timthumb(path, log, debug):
    new_path = path + '.old'
    print 'Old path %s\n' % path
    cache = ''
    newline = ''
    shutil.copy(path, new_path)
    proper_file = open(path, 'w')
    for line in open(new_path, 'r'):
        if '$cache_dir = \'' in line:
            if debug:
                print 'Starting our search for cache dir'
            firstq = line.find('\'')
            semic = line.rfind(';$')
            cache = line[firstq+1:semic-2] 
            if debug:
                print 'Old Cache dir is %s\n' % cache
    
    tmppath = path + '.tmp'
    new_thumb = urllib.urlretrieve('http://timthumb.googlecode.com/svn/trunk/timthumb.php', tmppath)
    tmpf = open(tmppath, 'r')
    realf = open(path, 'w')
    newline = ''
    for line in open(tmppath, 'r'):
        if 'FILE_CACHE_DIRECTORY' in line:
            if 'define' in line:
	        newline =  line.replace('./cache', cache)
                if debug:
                    print newline 
        else:
            newline = line 
        realf.write(newline)
    tmpf.close()
    realf.close()
    os.unlink(tmppath)
    if debug:
        print 'New path %s\n' % new_path 
    logfile = open(log, 'a')
    logfile.write('Replaced ')
    logfile.write(path)
    logfile.write(' with current version\n')
    return 1

def print_help():
    sys.stderr.write("--log option should be the logfile you want to output to\n");
    sys.exit(1)

if __name__ == '__main__':
    debug = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "lhd", ['log=', 'debug', 'help'])
    except getopt.GetoptError, err:
        print str(err)
        print_help()
        sys.exit(2)
    log = '/var/log/timthumb.log'
    # go through o (option) and a (arugment)
    # set accordingly
    for o, a in opts:
        if o in ('-l', '--log'):
            log = a
        elif o in ('-h', '--help'):
            print_help()
        elif o in ('-d', '--debug'):
            debug = True 
        else:
           assert False, 'unhandled option'
    path = '/var/www/'
    for site in os.listdir(path):
        print "Found a vhost %s" % site
        goto = os.path.join(path, site)
        print "Your path is %s\n" % goto
        if os.path.isdir(goto):
            walktree(goto, log, debug)

