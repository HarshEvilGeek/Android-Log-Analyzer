import sys
import zipfile
import re
import os

#configure these lines according to the app you wish to analyze
app_marker_name = 'com.fiberlink'
key_word_agent = 'agent'
key_word_docs = 'docs'
key_word_pim = 'pim'
key_word_device_info = 'device'

#standard constants
cmd_marker = 'Cmd line: '
key_word_anr = 'anr'
key_word_migration = 'migra'
key_word_wait = 'WAIT'
key_word_thread_id = 'tid='
key_word_held_by = 'held by tid='
key_word_dalvik_threads = 'DALVIK THREADS'
key_word_native_threads = 'NATIVE THREADS'
key_word_main = '"main"'

#global variables
map = {}
matchesMap = {}

def stripByteArrayString(line):
    line = line.replace('\\t', '    ')
    line = line.replace('\\r','')
    line = line.replace('b\'','')
    line = line.replace('\'','')
    line = line.replace('\\n','')
    line = line.replace('\\r','')
    return line

def processAnr(filename, logfile):
    f = logfile.open(filename, 'r')
    currentapp = ''
    ourapp = False
    issue = False
    ismain = False
    currentthread = -1
    threadtype = ''
    deadlockoccured = False
    deadlock = [] 
    finaldeadlock = []
    deadlockapp = ''
    mainwait = ''
    mainheldby = ''
    threadstate = ''
    threadwait = {}
    threadstoprint = []
    firstapplines = []
    threadregex = re.compile('.*".+".*prio=\d+.*tid=\d+.*')
    for line in f:
        line = str(line)
        if cmd_marker in line:
            currentapp = stripByteArrayString(line[line.index(cmd_marker) + len(cmd_marker):])
            threadwait = {}
            if currentapp.startswith(app_marker_name):
                ourapp = True
        if ourapp and ismain and app_marker_name in line:
            firstapplines.append(stripByteArrayString(line)[2:])
        elif key_word_dalvik_threads in line:
            threadtype = 'Dalvik'
        elif key_word_native_threads in line:
            threadtype = 'Native'
        elif re.match(threadregex, line):
            analyze = line[line.index(key_word_thread_id):]
            currentthread = int(re.findall('\d+',analyze)[0])
            threadstate = re.findall('[A-Z]+',analyze)[0]
            if key_word_main in line:
                ismain = True
                if threadstate is key_word_wait:
                    identifier = (currentapp, currentthread)
                    threadstoprint.append(identifier)
                    mainwait = currentapp
            else:
                ismain = False
        if key_word_held_by in line:
            analyze = line[line.index(key_word_held_by):]
            heldby = int(re.findall('\d+',analyze)[0])
            threadwait[currentthread] = heldby
            lookfor = [currentthread]
            if currentthread is not heldby and threadtype is not 'Native':
                if ismain:
                    mainheldby = heldby
                try:
                    identifier = (currentapp, currentthread)
                    threadstoprint.append(identifier)
                    deadlock.append(identifier)
                    identifier = (currentapp, heldby)
                    threadstoprint.append(identifier)
                    deadlock.append(identifier)

                    while heldby is not threadwait[heldby]:
                        lookfor.append(heldby)
                        heldby = threadwait[heldby]
                        identifier = (currentapp, heldby)
                        threadstoprint.append(identifier)
                        deadlock.append(identifier)
                        if heldby in lookfor:
                            if mainheldby is not '':
                                if mainheldby in deadlock or not finaldeadlock:
                                    finaldeadlock = deadlock
                                    deadlockapp = currentapp
                            else:
                                finaldeadlock = deadlock
                                deadlockapp = currentapp
                            deadlock = []
                            deadlockoccured = True
                            break
                        else:
                            deadlockoccured = False;
                    if not deadlockoccured:
                        deadlock = []
                except:
                    deadlock = []
    
    print('Most likely cause of ANR:\n')
    if len(finaldeadlock) > 0:
        print('Deadlock has occured in ' + deadlockapp + '\n')
        last = len(finaldeadlock) - 1
        deadlockedthreads = []
        for i in range (0, len(finaldeadlock)):
            deadlockedthreads.append(finaldeadlock[i][1])
            if i == last:
                print ('thread number ' + str(finaldeadlock[i][1]))
            elif i == 0:
                print ('Thread number ' + str(finaldeadlock[i][1]) + ' was held by '),
            else:
                print ('Thread number ' + str(finaldeadlock[i][1]) + ' which was held by '),
        
        if mainheldby is not '' and mainheldby in deadlockedthreads:
            print ('main thread is held by ' + str(mainheldby) + ' which is deadlocked ')

    elif mainwait:
        print('Main thread of ' + mainwait + ' is waiting\n')
    else:
        print('Heavy operations on UI. Might be caused from the following classes:\n')
        for line in firstapplines:
            print(line)

    p = False
    print ('\nThreads to look at:\n')
    f = logfile.open(filename, 'r')
    for line in f:
        line = str(line)
        if cmd_marker in line:
            currentapp = stripByteArrayString(line[line.index(cmd_marker) + len(cmd_marker):])
        elif re.match(threadregex, line):
            analyze = line[line.index(key_word_thread_id):]
            currentthread = int(re.findall('\d+',analyze)[0])
            identifier = (currentapp, currentthread)
            if identifier in threadstoprint:
                print('In app ' + currentapp + ':')
                p = True
            else:
                p = False
        if p:
            print (stripByteArrayString(line))
    
def processLog(filename, logfile):
    p = False
    f = logfile.open(filename, 'r')
    found = False
    end = re.compile('.*\d+\-\d+\-\d.*')

    for line in f:
        line = str(line)
        if end.match(line):
            if p:
                print('\n\n')
                p = False
        if 'UNCAUGHT EXCEPTION' in line:
            p = True
            print ('\nUncaught Exception in file ' + filename + '\n')
            found = True
        if p:
            line = stripByteArrayString(line) 
            print(line)
        for key in matchesMap:
            if key in line:
                line = stripByteArrayString(line)
                time = line.split(' |')[0]
                matchesMap[key].append(time);
    if not found:
        print('No uncaught exceptions in file ' + filename + '\n')
    
def processDeviceLog(filename, logfile):
    with logfile.open(filename, 'r') as f:
        for line in f:
            line = str(line)
            line = stripByteArrayString(line)
            print(line)

def main():
    printdevicedata = False;
    if (len(sys.argv) < 2):
        print('Please pass the path of the zipped log file or log folder as an argument')
        return

    logfile = ''

    f = open('map.txt', 'r')
    for line in f:
        temp = [x.strip() for x in line.split(':')]
        map[temp[0]] = temp[1]
        matchesMap[temp[1]] = []

    f.close()
    if os.path.isdir(sys.argv[1]):
        logfile = zipfile.ZipFile(sys.argv[1] + '.zip', 'w')
        for dirname, subdirs, files in os.walk(sys.argv[1]):
            logfile.write(dirname)
            for filename in files:
                logfile.write(os.path.join(dirname, filename))
    elif 'zip' in sys.argv[1]:
        logfile = zipfile.ZipFile(sys.argv[1])
    else: 
        logfile = zipfile.ZipFile('logs.zip', 'w')
        logfile.write(sys.argv[1])

    files = logfile.namelist()
        
    anr = False
    migration = False
    pim = False
    docs = False

    for filename in files:
        if key_word_device_info in filename and printdevicedata:
            print('Device Info\n')
            processDeviceLog(filename, logfile)
        if key_word_anr in filename:
            anr = True
        if key_word_migration in filename:
            migration = True
        if key_word_pim in filename:
            pim = True
        if key_word_docs in filename:
            docs = True

    if anr:
        print('\nProcessing ANR Logs\n')
        for filename in files:
            if key_word_anr in filename:
                processAnr(filename, logfile)

    if migration:
        print('\nProcessing Migration Logs\n')
        for filename in files:
            if key_word_migration in filename:
                processLog(filename, logfile)

    print('\nProcessing Agent Logs\n')
    for filename in files:
        if key_word_agent in filename:
            processLog(filename, logfile)

    if pim:
        print('\nProcessing PIM Logs\n')
        for filename in files:
            if key_word_pim in filename:
                processLog(filename, logfile)

    if docs:
        print('\nProcessing Docs Logs\n')
        for filename in files:
            if key_word_docs in filename:
                processLog(filename, logfile)

    for key in map:
        temp = matchesMap[map[key]]
        if (len(temp) > 0):
            sys.stdout.write (key + ': ' + str(len(temp)) + ' occurences at ')
            last = len(temp) - 1
            for i in range (0, len(temp)):
                if i == last:
                    print ('and ' + temp[i] + '\n')
                else:
                    sys.stdout.write (temp[i] + ', ')
    logfile.close()
            
if __name__ == '__main__':
    main()
