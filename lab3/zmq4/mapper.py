import pickle
import sys
import time

import zmq

import constPipe

me = str(sys.argv[1])
address_splt = "tcp://" + constPipe.SPLITTER_ADR + ":" + constPipe.SPLITTER_PRT
address_push1 = "tcp://localhost" + ":" + constPipe.MAPPER_TREE[me]["1"]
address_push2 = "tcp://localhost" + ":" + constPipe.MAPPER_TREE[me]["2"]

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)
push_socket1 = context.socket(zmq.PUSH)
push_socket2 = context.socket(zmq.PUSH)

pull_socket.connect(address_splt)
push_socket1.bind(address_push1)
push_socket2.bind(address_push2)

time.sleep(1)

print("{} started".format(me))

while True:
        work = pickle.loads(pull_socket.recv())
        print("{} received workload from {}".format(me, work[0]))
        words = work[1].split()
        for word in words:
                word_hash = hash(word)
                if(word_hash % 2 == 0):
                        push_socket1.send(pickle.dumps((me,word)))
                else:
                        push_socket2.send(pickle.dumps((me,word)))


