import time
import rpc
import logging
import threading

from context import lab_logging

def show_rpc_result(cl, result):
    print("Result: {}".format(result.value))

lab_logging.setup(stream_level=logging.INFO)

cl = rpc.Client()
cl.run()

base_list = rpc.DBList({'foo'})

cl.append_async('bar', base_list, show_rpc_result)

while cl.active_threads > 0:
    cl.ping()
    time.sleep(1)

cl.stop()
