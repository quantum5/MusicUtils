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
            self.instrument(data)
        elif head == 'SPEED':
            try:
                self.tempo(float(data))
            except ValueError as e:
                print 'Bad Speed Indicater:', e.message
        elif head == 'LYRICS':
            self.lyrics(data.lower() in ('on', 'yes', 'da', '1', 'true'))
        elif head == 'L':
            self.say(data.replace('\\n', '\n')
                         .replace('\\b', '\b')
                         .replace('\\r', '\r'))
        elif head == 'V':
            self.dynamic(data)
        else:
            self.play(head, data)
    
    def instrument(self, new):
        raise NotImplementedError
    
    def tempo(self, new):
        raise NotImplementedError
    
    def lyrics(self, new):
        raise NotImplementedError
    
    def say(self, new):
        raise NotImplementedError
    
    def dynamic(self, new):
        raise NotImplementedError
    
    def play(self, new):
        raise NotImplementedError
    
    def run(self):
        fails = 0
        self.queue = Queue()
        
        with self.file as file:
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
