import sys
import time
from Queue import Queue
from threading import Thread

from musicparser import Parser
from mediatimer import MediaTimer
from beep import Beeper
from midi import MIDI

class Player(Parser):
    def __init__(self, *args, **kwargs):
        super(Player, self).__init__(*args, **kwargs)
        self.player = Beeper()
        self.speed = 2000
        self.noteinfo = True
    
    def instrument(self, new, channel):
        if channel != 0:
            if not isinstance(self.player, MIDI):
                self.player = MIDI()
            self.player.type(new, channel)
            return
        self.player.close()
        if new.strip().lower().startswith('beep'):
            self.player = Beeper()
            self.filter.discard('%')
            self.strip.discard('$')
            self.filter.add('$')
            self.strip.add('%')
        else:
            self.player = MIDI()
            self.filter.discard('$')
            self.strip.discard('%')
            self.filter.add('%')
            self.strip.add('$')
            try:
                self.player.type(new)
            except ValueError as e:
                # Fallback to Beeper
                print e.message
                self.player.close()
                self.player = Beeper()
                self.filter.discard('%')
                self.strip.discard('$')
                self.filter.add('$')
                self.strip.add('%')
    
    def tempo(self, new):
        self.speed = new
    
    def lyrics(self, new):
        self.noteinfo = not new
    
    def say(self, new):
        self.write(new, newline=False)
    
    def dynamic(self, new, channel):
        self.player.dynamic(new)
    
    def noteon(self, channel, note):
        self.player.on(channel, note)
    
    def noteoff(self, channel, note):
        self.player.off(channel, note)
    
    def play(self, head, data):
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
                sys.stdout.write(item)
            except IOError:
                pass
    
    def write(self, *args, **kwargs):
        self.queue.put(kwargs.get('sep', '').join(i if isinstance(i, unicode) else unicode(i) for i in args))
        if kwargs.get('newline', True):
            self.queue.put('\n')
    
    def run(self):
        self.queue = Queue()
        thread = Thread(target=self.writer)
        thread.daemon = True
        thread.start()
        
        try:
            with MediaTimer():
                super(Player, self).run()
        finally:
            self.queue.put(None)

def main():
    import sys
    import codecs
    sys.stdout = codecs.getwriter(sys.stdout.encoding)(sys.stdout, 'backslashreplace')
    
    for file in sys.argv[1:]:
        try:
            player = Player(open(file))
        except IOError as e:
            print e.message, 'on opening:', file
        else:
            player.run()

if __name__ == '__main__':
    main()
