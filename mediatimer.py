from ctypes import windll

process = windll.kernel32.GetCurrentProcess()

GetPriorityClass = windll.kernel32.GetPriorityClass
SetPriorityClass = windll.kernel32.SetPriorityClass
timeBeginPeriod = windll.winmm.timeBeginPeriod
timeEndPeriod = windll.winmm.timeEndPeriod

class MediaTimer(object):
    def __init__(self, precision=1, priority=0x80):
        self.precision = precision
        self.priority = priority
    
    def __enter__(self):
        timeBeginPeriod(self.precision)
        self.old_priority = GetPriorityClass(process)
        SetPriorityClass(process, self.priority)
    
    def __exit__(self, exc_type, exc_value, traceback):
        timeEndPeriod(self.precision)
        SetPriorityClass(process, self.old_priority)
