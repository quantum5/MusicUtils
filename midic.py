from midi import miditable, instruments, dynamics
from musicparser import Parser

import sys
from textwrap import dedent

class MusicToMidiC(Parser):
    def __init__(self, file, stream=None, rawapi=False):
        super(MusicToMidiC, self).__init__(file)
        self.speed = 2000
        self.force = 0x40
        self.stream = stream or sys.stdout
        self.rawapi = rawapi
        self.message = 0
        self.to_print = []

        self.filter.discard('$')
        self.strip.discard('%')
        self.filter.add('%')
        self.strip.add('$')
    
    def instrument(self, new, channel):
        try:
            try:
                id = int(new, 0)
            except ValueError:
                try:
                    id = instruments[new]
                except KeyError:
                    raise ValueError('Invalid Instrument')
            if 0 < id < 0x80:
                self.stream.write('M(%x)' % (id << 8 | 0xC0 | channel))
                self.message += 1
            else:
                raise ValueError('Instrument %s out of range' % new)
        except ValueError as e:
            self.stream.write('/* %s */' % e.message)
    
    def tempo(self, new):
        self.speed = new
    
    def lyrics(self, new):
        pass
    
    def say(self, new):
        self.to_print.append((self.message, new.replace('"', '\\"')
                                               .replace('\n', '\\n')
                                               .replace('\b', '\\b')
                                               .replace('\r', '\\r')))
        return
        print >>self.stream, '\tprintf("%%s", "%s");' % (new.replace('"', '\\"')
                                             .replace('\n', '\\n')
                                             .replace('\b', '\\b')
                                             .replace('\r', '\\r'))
    
    def dynamic(self, new, channel):
        try:
            force = int(new, 0)
        except ValueError:
            try:
                force = dynamics[new]
            except KeyError:
                self.stream.write('/* Dynamic Invalid: %s */' % new)
        if 0 < force < 0x80:
            self.force = force
        else:
            self.stream.write('/* Dynamic %s out of range */' % new)
    
    def play(self, head, data):
        try:
            length = float(data.rstrip('+'))
        except ValueError:
            self.stream.write('/* %s not known */' % data)
            return
        length = self.speed / length
        
        if data.endswith('+'):
            # Dotted notes
            length *= 1.5
        
        if head.startswith('0'):
            self.stream.write('S(%d)' % length)
            self.message += 1
            return
        
        if ',' in head:
            notes = head.split(',')
        else:
            notes = [head]
        
        for note in notes:
            if note not in miditable:
                self.stream.write("/* %s doesn't exist in my world */" % head)
                continue
            self.stream.write('M(%x)' % (self.force << 16 | miditable[note] << 8 | 0x90))
            self.message += 1
        
        self.stream.write('S(%d)' % length)
        notes.reverse()
        
        for note in notes:
            if note not in miditable:
                continue
            self.stream.write('M(%x)' % (miditable[note] << 8 | 0x90))
            self.message += 1
        
        self.stream.write('S(10)')
        self.message += 2

    def noteon(self, channel, note):
        if note not in miditable:
            self.stream.write("/* %s doesn't exist in my world */" % note)
            return
        self.stream.write('M(%x)' % (self.force << 16 | miditable[note] << 8 | 0x90 | channel))
        self.message += 1
    
    def noteoff(self, channel, note):
        if note not in miditable:
            self.stream.write("/* %s doesn't exist in my world */" % note)
            return
        self.stream.write("M(%x)" % (miditable[note] << 8 | 0x90 | channel))
        self.message += 1

    def run(self):
        if self.rawapi:
            print >>self.stream, '/* To compile, use cl /GS- /O1',
            print >>self.stream, self.stream.name,
            print >>self.stream, '/link /nodefaultlib /entry:RawEntry',
            print >>self.stream, '/subsystem:CONSOLE kernel32.lib winmm.lib */'
        print >>self.stream, dedent('''\
            #include <windows.h>
            #include <wchar.h>
            #pragma comment(lib, "winmm.lib")
            HMIDIOUT handle;
            HANDLE worker;
            BOOL running = TRUE;

            DWORD WINAPI ThreadProc(LPVOID lpParameter);
            BOOL WINAPI HandlerRoutine(DWORD dwCtrlType);
            '''
        )
        if self.rawapi:
            print >>self.stream, 'DWORD WINAPI RawEntry()'
        else:
            print >>self.stream, 'int main(int argc, char *argv[])'
        print >>self.stream, '{'
        print >>self.stream, dedent('''\
                midiOutOpen(&handle, 0, 0, 0, CALLBACK_NULL);
                midiOutSetVolume(handle, 0x7FFF7FFF);
                SetPriorityClass(GetCurrentProcess(), 0x80);
                worker = CreateThread(NULL, 0, ThreadProc, NULL, 0, NULL);
                SetConsoleCtrlHandler(HandlerRoutine, TRUE);
                WaitForSingleObject(worker, INFINITE);
                ExitProcess(1);
            }

            BOOL WINAPI HandlerRoutine(DWORD dwCtrlType) {
                switch (dwCtrlType) {
                case CTRL_C_EVENT:
                    if (running) {
                        SuspendThread(worker);
                        midiOutSetVolume(handle, 0x00000000);
                    } else {
                        midiOutSetVolume(handle, 0x7FFF7FFF);
                        ResumeThread(worker);
                    }
                    running = !running;
                    return TRUE;
                default:
                    ExitProcess(0);
                    return FALSE;
                }
            }

            typedef struct {
                int offset;
                LPWSTR string;
            } LyricLine;

            #define M(m) 0x##m,
            #define L(m) 0x40##m,
            #define S(s) -s,
            INT messages[] = {'''
        )
        super(MusicToMidiC, self).run()
        print >>self.stream, dedent('''
            };
            #undef M
            #undef L
            #undef S

            static LyricLine lyrics[] = {'''
        )
        for id, string in self.to_print:
            print >>self.stream, '\t{%d, L"%s"},' % (id, string)
        print >>self.stream, dedent('''\
            };

            DWORD lyrics_count = %d;

            VOID WriteText(LPWSTR text) {''' % len(self.to_print)
        )
        if self.rawapi:
            print >>self.stream, dedent('''\
                HANDLE hStdout = GetStdHandle(STD_OUTPUT_HANDLE);
                DWORD count = WideCharToMultiByte(CP_OEMCP, 0, text, -1, NULL, 0, NULL, NULL);
                LPSTR storage = (LPSTR) HeapAlloc(GetProcessHeap(), 0, count);
                if (storage) {
                    if (WideCharToMultiByte(CP_OEMCP, 0, text, -1, storage, count, NULL, NULL)) {
                        WriteFile(hStdout, storage, lstrlenA(storage), &count, NULL);
                    }
                    HeapFree(GetProcessHeap(), 0, storage);
                }
            }''')
        else:
            print >>self.stream, '    wprintf(L"%s", text);\n}'
        print >>self.stream, dedent('''
            DWORD WINAPI ThreadProc(LPVOID lpParameter) {
                DWORD i;
                BOOL has_lyrics = lyrics_count != 0;
                DWORD lyric_id = 0;
                DWORD offset;
                if (has_lyrics)
                    offset = lyrics[0].offset;
                for (i = 0; i < %d; ++i) {
                    if (has_lyrics && lyric_id < lyrics_count) {
                        if (i >= offset) {
                            WriteText(lyrics[lyric_id++].string);
                            offset = lyrics[lyric_id].offset;
                        }
                    }
                    if (messages[i] < 0) {
                        int time = -messages[i];
                        int period;
                        if (time < 2)
                            period = 1;
                        else if (time < 10)
                            period = 2;
                        else if (time < 30)
                            period = 5;
                        else if (time < 50)
                            period = 10;
                        else
                            period = 15;
                        
                        timeBeginPeriod(period);
                        Sleep(time);
                        timeEndPeriod(period);
                    } else
                        midiOutShortMsg(handle, messages[i]);
                }
                for (; lyric_id < lyrics_count; ++lyric_id) {
                    WriteText(lyrics[lyric_id].string);
                }
                midiOutClose(handle);
                return 0;
            }''' %
            self.message
        )

def main():
    import sys
    import codecs
    
    for file in sys.argv[1:]:
        try:
            converter = MusicToMidiC(open(file), codecs.open(file.rsplit('.', 1)[0]+'.c', 'wb', 'utf-8'), rawapi=True)
        except IOError as e:
            print e.message, 'on opening:', file
        else:
            converter.run()

if __name__ == '__main__':
    main()
