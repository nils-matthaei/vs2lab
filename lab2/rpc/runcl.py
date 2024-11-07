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

append_thread = threading.Thread(target=cl.append, args=('bar', base_list, show_rpc_result))
append_thread.start()


for i in range(11):
    print(f"Client still active [{i}]")
    time.sleep(1)

cl.close()

# Unklar: Wann client schliessen?
# Entweder im callback oder so wie aktuell implementiert (Wenn der Client vor dem return des callbacks geschlossen wird, stuerzt der Server ab)
# Alternativ: Client laeuft im endless loop bis der callback zurueckkommt