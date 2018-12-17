import threading

from flask_server import StartFlask
from recognize import StartRecognition

def main():
    thread_flask = threading.Thread(target=StartFlask)
    thread_recogn = threading.Thread(target=StartRecognition)
    thread_flask.start()
    thread_recogn.start()


if __name__ == '__main__':
    main()
