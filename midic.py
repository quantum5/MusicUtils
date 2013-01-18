from midi import miditable, instruments, dynamics
from musicparser import Parser
import sys

class MusicToMidiC(Parser):
    def __init__(self, file, stream=None):
        super(MusicToMidiC, self).__init__(file)
        self.speed = 2000
        self.force = 0x40
        self.stream = stream or sys.stdout
    
    def instrument(self, new):
        try:
            try:
                id = int(new, 0)
            except ValueError:
                try:
                    id = instruments[new]
                except KeyError:
                    raise ValueError('Invalid Instrument')
            if 0 < id < 0x80:
                print >>self.stream, '\tmidiOutShortMsg(h, 0x%x);'%(id << 8 | 0xC0)
            else:
                raise ValueError('Instrument %s out of range' % new)
        except ValueError as e:
            print >>self.stream, '//', e.message
    
    def tempo(self, new):
        self.speed = new
    
    def lyrics(self, new):
        pass
    
    def say(self, new):
        print >>self.stream, '\tprint >>self.stream,f("%%s", "%s");' % (new.replace('"', '\\"')
                                             .replace('\n', '\\n')
                                             .replace('\b', '\\b')
                                             .replace('\r', '\\r'))
    
    def dynamic(self, new):
        try:
            force = int(new, 0)
        except ValueError:
            try:
                force = dynamics[new]
            except KeyError:
                print >>self.stream, '// Dynamic Invalid: %s' % new
        if 0 < force < 0x80:
            self.force = force
        else:
            print >>self.stream, '// Dynamic %s out of range' % new
    
    def play(self, head, data):
        try:
            length = float(data.rstrip('+'))
        except ValueError:
            print >>self.stream, '//', data, 'not known'
            return
        length = self.speed / length
        
        if data.endswith('+'):
            # Dotted notes
            length *= 1.5
        
        if head.startswith('0'):
            print >>self.stream, '\tSleep(%d);' % length
            return
        
        if head not in miditable:
            print >>self.stream, "// %s doesn't exist in my world" % head
            return
        
        print >>self.stream, '''\
\tmidiOutShortMsg(h, 0x%x);
\tSleep(%d);
\tmidiOutShortMsg(h, 0x%x);
\tSleep(10);''' % (self.force << 16 | miditable[head] << 8 | 0x90, length,
                 miditable[head] << 8 | 0x90)

    def run(self):
        print >>self.stream, '#include <windows.h>'
        print >>self.stream
        print >>self.stream, 'int main(int argc, char *argv[]) {'
        print >>self.stream, '\tHMIDIOUT h;'
        print >>self.stream, '\ttimeBeginPeriod(1);'
        print >>self.stream, '\tSetPriorityClass(GetCurrentProcess(), 0x80);'
        print >>self.stream, '\tmidiOutOpen(&h, 0, 0, 0, 0);'
        super(MusicToMidiC, self).run()
        print >>self.stream, '\tmidiOutClose(h);'
        print >>self.stream, '\ttimeEndPeriod(1);'
        print >>self.stream, '}'

def main():
    import sys
    import codecs
    
    for file in sys.argv[1:]:
        try:
            converter = MusicToMidiC(open(file), codecs.open(file.rsplit('.', 1)[0]+'.c', 'wb', 'utf-8'))
        except IOError as e:
            print e.message, 'on opening:', file
        else:
            converter.run()

if __name__ == '__main__':
    main()
