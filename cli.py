from player import Player

def main():
    import sys
    import codecs
    sys.stdout = codecs.getwriter('mbcs')(sys.stdout, 'backslashreplace')
    
    for file in sys.argv[1:]:
        try:
            player = Player(open(file))
        except IOError as e:
            print e.message, 'on opening:', file
        else:
            player.run()

if __name__ == '__main__':
    main()
