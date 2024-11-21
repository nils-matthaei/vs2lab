import pickle
import zmq
import constPipe
import time

src = constPipe.SPLITTER_ADR
prt = constPipe.SPLITTER_PRT
me = "s1"

context = zmq.Context()
push_socket = context.socket(zmq.PUSH)

address = "tcp://" + src + ":" + prt
push_socket.bind(address)

time.sleep(1)

def distribute_sentence(sentence):
    push_socket.send(pickle.dumps((me, sentence)))


def process_file(file_path):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                distribute_sentence(line.strip())
    except FileNotFoundError:
        print(f"The file at {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


process_file("input.txt")
