'''
Created on Nov 30, 2017

@author: seth_
'''
import sys
sys.path.append("..")
from MobileCodeService import MobileCodeClient, MobileCodeServerTracker
from MobileCodeService import MobileCodeServer, DiscoveryResponder
from MobileCodeService.Auth import NullClientAuth, NullServerAuth
from MobileCodeService.Engine import DefaultMobileCodeEngine
from MobileCodeService.Wallet import NullClientWallet, NullServerWallet
import playground, os, subprocess, time, sys
from asyncio.events import get_event_loop

class ClientControl:
    def __init__(self):
        self.tracker = MobileCodeServerTracker()
        self.tracker.registerListener(self.serverFound)
        
    def serverFound(self, address, port):
        print("Tracker found address at {}:{}".format(address, port))
        print("One is enough.")
        get_event_loop().call_soon(self.tracker.unregisterListener, self.serverFound)
        self.runCodeAndPrintResult(MobileCodeClient("default", address, port, samplecode, NullClientAuth(), NullClientWallet()))
    
    def runCodeAndPrintResult(self, client):
        future = client.run()
        future.add_done_callback(lambda f: print(f.result()))

if __name__=="__main__":
    from playground.common.logging import EnablePresetLogging, PRESET_DEBUG
    EnablePresetLogging(PRESET_DEBUG)
    
    samplecode = "print('this is a test')"
    serverWallet = NullServerWallet()
    serverAuth = NullServerAuth()
    serverEngine = DefaultMobileCodeEngine()
    serverFactory = lambda: MobileCodeServer(serverWallet, serverAuth, serverEngine)
    #
    control = ClientControl()
    coro = playground.getConnector().create_playground_server(serverFactory, 1)
    loop = get_event_loop()
    server = loop.run_until_complete(coro)
    print("Server started", server)
    serverAddress, serverPort = server.sockets[0].gethostname()
    responder = DiscoveryResponder(serverAddress, serverPort, serverAuth)
    loop.call_soon(responder.start)
    loop.call_later(2.0, control.tracker.sendPing)
    print("Start loop")
    loop.run_forever()