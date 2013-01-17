from beep import table

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
        print '\tprintf("%%s", "%s");' % new.replace('"', '\\"')
    
    def dynamic(self, new):
        self.player.dynamic(new)
    
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
            time.sleep(length/1000.)
            return
        
        print '\tBeep(%d, %d)' % (int(table[head]), length)
    
    def run(self):
        print '#include <windows.h>'
        print
        print 'int main(int argc, char *argv[]) {'
        super(MusicToC, self).run()
        print '}'
