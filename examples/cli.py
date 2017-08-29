# -*- coding:utf-8 -*-
from sulley import *
import binascii
import time

class Fuzzer(object):
    def __init__(self):
        pass

    def set_mutate_frame_callback(self):
        return "afl"

    def post_mutate_callback(self, block):
        while True:
            payload = block.render()
            payload += '\n'
            # payload = "hostname " + payload
            block.set_mutate_payload(payload)

            if payload[0].lower() == 'q' or payload[0].lower() == 'e':
                block.mutate()
                continue
            else:
                break
        print "fuzz data length: %d" % len(block.render())

    def connect_success_callback(self, sock, target):
        time.sleep(0.2)
        print sock.recv(1000)
        sock.send("admin\n")
        time.sleep(0.2)
        print sock.recv(1000)
        sock.send("123\n")
        time.sleep(0.2)
        print sock.recv(1000)
        sock.send("sys\n")
        return False


    def post_send_callback(self, sock, data, fuzzStoreList):
        reconn = False
        sock.settimeout(2)
        try:
            buf = sock.recv(65536)
            print "Recv length: %d. Payload: %s" % (len(buf), buf)
            if len(buf) <= 0:
                reconn = True
        except Exception, e:
            print "recv error. Exception: %s" % str(e)

        return (reconn, False, False)

    def detect_target_crash_callback(self, fuzzStoreList):
        print binascii.b2a_hex(fuzzStoreList[-1])
        file = open("crash_data.txt", "w")
        for data in fuzzStoreList:
            file.write(binascii.b2a_hex(data) + "\n")
            file.flush()
        file.close()
        return False

if __name__ == '__main__':
    fuzz = Fuzzer()
    sess = sessions.session(proto="tcp", keep_alive=True, pinger_threshold=1000, sock_timeout=3,
                            fuzz_store_limit=10000, loop_sleep_time=0.0005)

    sess.set_mutate_frame_callback          = fuzz.set_mutate_frame_callback
    sess.post_mutate_callback               = fuzz.post_mutate_callback
    sess.detected_target_crash_callback     = fuzz.detect_target_crash_callback
    sess.connect_success_callback           = fuzz.connect_success_callback
    sess.post_send_callback                 = fuzz.post_send_callback

    target = sessions.target("192.168.1.2", 23)
    afl_block = ex_afl.AFL("CLI_FUZZ", "in")
    sess.add_afl_block(afl_block)
    sess.add_target(target)

    sess.fuzz()
