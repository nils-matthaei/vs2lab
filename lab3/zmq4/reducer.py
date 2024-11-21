import pickle
import sys
import time

import zmq

import constPipe

counter = 0

me = str(sys.argv[1])

src = constPipe.MAPPER_ADR1
ports = [
    constPipe.MAPPER_PRT1_1 if me == 'r1' else constPipe.MAPPER_PRT1_2,
    constPipe.MAPPER_PRT2_1 if me == 'r1' else constPipe.MAPPER_PRT2_2,
    constPipe.MAPPER_PRT3_1 if me == 'r1' else constPipe.MAPPER_PRT3_2
]

addresses = [f"tcp://{src}:{port}" for port in ports]

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)

for address in addresses:
    pull_socket.connect(address)

time.sleep(1)

print("{} started".format(me))

while True:
    work = pickle.loads(pull_socket.recv())
    print("{} received word {} from {}".format(me, work[1], work[0]))
    counter += 1
    print(f'Count: {counter}', end='\r')


