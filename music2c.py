from beep import table
from musicparser import Parser

class MusicToC(Parser):
    def __init__(self, *args, **kwargs):
        super(MusicToC, self).__init__(*args, **kwargs)
        self.speed = 2000
    
    def instrument(self, new):
        pass
    
    def tempo(self, new):
        self.speed = new
    
    def lyrics(self, new):
        pass
    
    def say(self, new):
        print '\tprintf("%%s", "%s");' % (new.replace('"', '\\"')
                                             .replace('\n', '\\n')
                                             .replace('\b', '\\b')
                                             .replace('\r', '\\r'))
    
    def dynamic(self, new):
        pass
    
    def play(self, head, data):
        try:
            length = float(data.rstrip('+'))
        except ValueError:
            print '//', data, 'not known'
            return
        length = self.speed / length
        
        if data.endswith('+'):
            # Dotted notes
            length *= 1.5
        
        if head.startswith('0'):
            print '\tSleep(%d);' % length
            return
        
        print '\tBeep(%d, %d);' % (int(table[head]), length)
    
    def run(self):
        print '#include <windows.h>'
        print
        print 'int main(int argc, char *argv[]) {'
        super(MusicToC, self).run()
        print '}'

def main():
    import sys
    import codecs
    sys.stdout = codecs.getwriter('mbcs')(sys.stdout, 'backslashreplace')
    
    for file in sys.argv[1:]:
        try:
            converter = MusicToC(open(file))
        except IOError as e:
            print e.message, 'on opening:', file
        else:
            converter.run()

if __name__ == '__main__':
    main()
