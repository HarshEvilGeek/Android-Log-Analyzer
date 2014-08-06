import sys
import zipfile
import re

app_marker_name = ‘<app name>’
cmd_marker = 'Cmd line: '
key_word_device_info = 'device'
key_word_anr = 'anr'
key_word_migration = 'migra'
key_word_agent = 'agent'
key_word_wait = 'WAIT'
key_word_thread_id = 'tid='
key_word_held_by = 'held by tid='
key_word_dalvik_threads = 'DALVIK THREADS'
key_word_native_threads = 'NATIVE THREADS'
key_word_main = '"main"'


def stripByteArrayString(line):
	line = line.replace('\\t', '	')
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
	deadlock = () 
	mainwait = ''
	threadstate = ''
	threadwait = {}
	threadstoprint = ()
	threadregex = re.compile('.*".+".*prio=\d+.*tid=\d+.*')
	for line in f:
		line = str(line)
		if cmd_marker in line:
			currentapp = stripByteArrayString(line[line.index(cmd_marker) + len(cmd_marker):])
			threadwait = {}
			if currentapp.startswith(app_marker_name):
				ourapp = True
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
				if threadstate = key_word_wait:
					identifier = (currentapp, currentthread)
					threadstoprint.add(identifier)
					mainwait = currentapp
		elif key_word_held_by in line:
			analyze = line[line.index(key_word_held_by):]
			heldby = int(re.findall('\d+',analyze)[0])
			threadwait[currentthread] = heldby
			if currentthread not = heldby and threadtype not 'Native':
				try:
					identifier = (currentapp, currentthread)
					threadstoprint.add(identifier)
					deadlock.add(identifier)
					identifier = (currentapp, heldby)
					threadstoprint.add(identifier)
					deadlock.add(identifier)

					while threadwait[heldby] not = heldby:
						heldby = threadwait[heldby]
						identifier = (currentapp, heldby)
						threadstoprint.add(identifier)
						deadlock.add(identifier)
						if heldby = currentthread:
							deadlockoccured = True
					if not deadlockoccured
						deadlock = ()
				except:
					deadlock = ()
	
	badopsonui = False
	print('\nMost likely cause of ANR:')
	if len(deadlock) > 0:
		print('Deadlock has occured\n')
	elif mainwait:
		print('Main thread of ' + mainwait + ' is waiting')
	else:
		print('Heavy operations on UI')
		badopsonui = True
	
def processLog(filename, logfile):
	p = False
	f = logfile.open(filename, 'r')

	end = re.compile('.*\d+\-\d+\-\d.*')
	for line in f:
		line = str(line)
		if end.match(line):
			if p:
				print('\n\n')
				p = 0
		if 'UNCAUGHT EXCEPTION' in line:
			p = 1
			print ('\nUncaught Exception in file ' + filename + '\n')
		if p:
			line = stripByteArrayString(line) 
			print(line)
		
	
def processDeviceLog(filename, logfile):
	with logfile.open(filename, 'r') as f:
		for line in f:
			line = str(line)
			line = stripByteArrayString(line)
			print(line)

def main():
	if (len(sys.argv) < 2):
		print('Please pass the path of the zipped log file as an argument')
		return
	logfile = zipfile.ZipFile(sys.argv[1])
	files = logfile.namelist()

	print("Device Info\n")
	for filename in files:
		if key_word_device_info in filename:
			processDeviceLog(filename, logfile)

	print("\nProcessing ANR Logs\n")
	for filename in files:
		if 'anr' in filename:
			processAnr(filename, logfile)

	print("\nProcessing Migration Logs\n")
	for filename in files:
		if key_word_migration in filename:
			processLog(filename, logfile)

	print("\nProcessing Agent Logs\n")
	for filename in files:
		if key_word_agent in filename:
			processLog(filename, logfile)
			
if __name__ == '__main__':
    main()
