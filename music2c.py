from beep import table
from musicparser import Parser

class MusicToC(Parser):
    def __init__(self, source, target):
        super(MusicToC, self).__init__(source)
        self.speed = 2000
        self.target = target
    
    def noteon(self, channel, note):
        pass
    
    def noteoff(self, channel, note):
        pass
    
    def instrument(self, new, channel):
        pass
    
    def tempo(self, new):
        self.speed = new
    
    def lyrics(self, new):
        pass
    
    def say(self, new):
        print>>self.target, '\tprintf("%%s", "%s");' % (new.replace('"', '\\"')
                                                           .replace('\n', '\\n')
                                                           .replace('\b', '\\b')
                                                           .replace('\r', '\\r'))
    
    def dynamic(self, new, channel):
        pass
    
    def play(self, head, data):
        try:
            length = float(data.rstrip('+'))
        except ValueError:
            print>>self.target, '//', data, 'not known'
            return
        length = self.speed / length
        
        if data.endswith('+'):
            # Dotted notes
            length *= 1.5
        
        if head.startswith('0'):
            print>>self.target, '\tSleep(%d);' % length
        else:
            print>>self.target, '\tBeep(%d, %d);' % (int(table[head.split(',')[0]]), length)
    
    def run(self):
        print>>self.target, '#include <windows.h>'
        print>>self.target
        print>>self.target, 'int main(int argc, char *argv[]) {'
        print>>self.target, '\ttimeBeginPeriod(1);'
        print>>self.target, '\tSetPriorityClass(GetCurrentProcess(), 0x80);'
        super(MusicToC, self).run()
        print>>self.target, '\ttimeEndPeriod(1);'
        print>>self.target, '}'

def main():
    import sys
    import codecs

    for file in sys.argv[1:]:
        try:
            converter = MusicToC(open(file), codecs.open(file.rsplit('.', 1)[0]+'.c', 'wb', 'utf-8'))
        except IOError as e:
            print e.message, 'on opening:', file
        else:
            converter.run()

if __name__ == '__main__':
    main()
