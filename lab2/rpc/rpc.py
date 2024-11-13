import time
import constRPC
import threading

from context import lab_channel


class DBList:
    def __init__(self, basic_list):
        self.value = list(basic_list)

    def append(self, data):
        self.value = self.value + [data]
        return self


class Client:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.client = self.chan.join('client')
        self.server = None
        self.ack_event = threading.Event()

    def run(self):
        self.chan.bind(self.client)
        self.server = self.chan.subgroup('server')

    def ping(self):
        print("Client is responsive...")

    def stop(self):
        self.chan.leave('client')

    def append(self, data, db_list, cb):
        assert isinstance(db_list, DBList)
        msglst = (constRPC.APPEND, data, db_list) 
        self.chan.send_to(self.server, msglst)
        msgrcv = self.chan.receive_from(self.server) 
        if(msgrcv[1] == constRPC.OK):
            self.ack_event.set()
        else:
            print(msgrcv) 
            
        res = self.chan.receive_from(self.server)
        cb(self, res[1])
        # return msgrcv[1]  # pass it to caller

    def append_async(self, data, db_list, cb):
        assert isinstance(db_list, DBList)

        ack_received_event = threading.Event()

        def run():
            msglst = (constRPC.APPEND, data, db_list)
            self.chan.send_to(self.server, msglst)
            print("Blocking until ACK")
            msgrcv = self.chan.receive_from(self.server)
            if msgrcv[1] == constRPC.OK:
                ack_received_event.set()
                print("ACK received")
            else:
                print(msgrcv)

            print("Thread is now waiting for server res...")
            res = self.chan.receive_from(self.server)
            cb(self, res[1])

        thread = threading.Thread(target=run)
        thread.start()

        ack_received_event.wait()


class Server:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.server = self.chan.join('server')
        self.timeout = 3

    @staticmethod
    def append(data, db_list):
        assert isinstance(db_list, DBList)  # - Make sure we have a list
        return db_list.append(data)

    def run(self):
        self.chan.bind(self.server)
        while True:
            msgreq = self.chan.receive_from_any(self.timeout)  # wait for any request
            if msgreq is not None:
                client = msgreq[0]  # see who is the caller
                msgrpc = msgreq[1]  # fetch call & parameters
                if constRPC.APPEND == msgrpc[0]:
                    time.sleep(5)
                    self.chan.send_to({client}, constRPC.OK)
                    time.sleep(10)
                    result = self.append(msgrpc[1], msgrpc[2])  # do local call
                    self.chan.send_to({client}, result)  # return response
                else:
                    pass  # unsupported request, simply ignore
