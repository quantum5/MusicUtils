import sys
import traceback

class Parser(object):
    def __init__(self, file):
        self.file = file
    
    def line(self, line):
        head, data = line.split(':', 1)
        data = data.lstrip(' ')
        head = head.upper()
        if head == 'INSTRUMENT':
            if ':' in data:
                channel, data = (i.strip() for i in data.split(':', 1))
                try:
                    channel = int(channel, 0)
                except ValueError:
                    print 'Bad channel id:', channel
                    channel = 0
            else:
                channel = 0
            self.instrument(data, channel)
        elif head == 'SPEED':
            self.tempo(float(data))
        elif head == 'LYRICS':
            self.lyrics(data.lower() in ('on', 'yes', 'da', '1', 'true'))
        elif head == 'L':
            self.say(data.replace('\\n', '\n')
                         .replace('\\b', '\b')
                         .replace('\\r', '\r'))
        elif head == 'V':
            if ':' in data:
                channel, data = (i.strip() for i in data.split(':', 1))
                try:
                    channel = int(channel, 0)
                except ValueError:
                    print 'Bad channel id:', channel
                    channel = 0
            else:
                channel = 0
            self.dynamic(data, channel)
        elif head in ('ON', 'OFF'):
            channel, note = (i.strip() for i in data.split(':', 1))
            try:
                channel = int(channel, 0)
            except ValueError:
                print 'Bad channel id:', channel
            else:
                (self.noteon if head == 'ON' else self.noteoff)(channel, note)
        else:
            self.play(head, data)
    
    def instrument(self, new, channel):
        raise NotImplementedError
    
    def tempo(self, new):
        raise NotImplementedError
    
    def lyrics(self, new):
        raise NotImplementedError
    
    def say(self, new):
        raise NotImplementedError
    
    def dynamic(self, new, channel):
        raise NotImplementedError
    
    def play(self, head, data):
        raise NotImplementedError
    
    def noteon(self, channel, note):
        raise NotImplementedError
    
    def noteoff(self, channel, note):
        raise NotImplementedError
    
    def run(self):
        fails = 0
        
        with self.file as file:
            for line in file:
                if line == '\n' or line.startswith((';', '#', '$', '!', '%', '/')):
                    continue
                try:
                    self.line(line.rstrip('\n').decode('utf-8', 'ignore'))
                except Exception:
                    traceback.print_exc()
                    fails += 1
                    if fails > 10:
                        print 'Too many errors'
                        return
