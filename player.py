import sys
import traceback
import time
from Queue import Queue
from threading import Thread

from mediatimer import MediaTimer
from beep import Beeper
from midi import MIDI

class Player(object):
    def __init__(self, file):
        self.file = file
        self.player = Beeper()
        self.speed = 2000
        self.noteinfo = True
    
    def line(self, line):
        head, data = line.split(':', 1)
        data = data.lstrip(' ')
        head = head.upper()
        if head == 'INSTRUMENT':
            self.player.close()
            if data.strip().lower().startswith('beep'):
                self.player = Beeper()
            else:
                self.player = MIDI()
                try:
                    self.player.type(data)
                except ValueError as e:
                    # Fallback to Beeper
                    print e.message
                    self.player.close()
                    self.player = Beeper()
        elif head == 'SPEED':
            try:
                self.speed = float(data)
            except ValueError as e:
                print 'Bad Speed Indicater:', e.message
        elif head == 'LYRICS':
            self.noteinfo = data.lower() in ('on', 'yes', 'da', '1', 'true')
        elif head == 'L':
            self.write(data.replace('\\n', '\n')
                           .replace('\\b', '\b')
                           .replace('\\r', '\r'),
                       newline=False)
        elif head == 'V':
            self.player.dynamic(data)
        else:
            try:
                length = float(data.rstrip('+'))
            except ValueError:
                print data, 'not known'
                return
            length = self.speed / length
            
            if data.endswith('+'):
                # Dotted notes
                length *= 1.5
            
            if head.startswith('0'):
                if self.noteinfo:
                    self.write('Sleep: ', length)
                time.sleep(length/1000.)
                return
            
            if self.noteinfo:
                self.write((head, length))
            self.player(head, length)
    
    def writer(self):
        while True:
            item = self.queue.get()
            if item is None:
                return
            try:
                sys.stdout.write(item.decode('utf-8', 'replace'))
            except IOError:
                pass
    
    def write(self, *args, **kwargs):
        self.queue.put(kwargs.get('sep', '').join(str(i) for i in args))
        if kwargs.get('newline', True):
            self.queue.put('\n')
    
    def run(self):
        fails = 0
        self.queue = Queue()
        thread = Thread(target=self.writer)
        thread.daemon = True
        thread.start()
        
        file = self.file
        try:
            with MediaTimer():
                for line in file:
                    if line == '\n' or line.startswith((';', '#', '$', '!', '%', '/')):
                        continue
                    try:
                        self.line(line.rstrip('\n'))
                    except Exception:
                        traceback.print_exc()
                        fails += 1
                        if fails > 10:
                            print 'Too many errors'
                            return
        finally:
            file.close()
            self.queue.put(None)
