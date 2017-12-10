from playground.network.common import StackingProtocolFactory

from ...lab_2.protocols import PEEPServer, PEEPClient, PassThroughProtocol
from  ..protocols import PLSPServer, PLSPClient

def get_lab3_server_factory():
    return StackingProtocolFactory(lambda: PLSPServer(), lambda: PEEPServer())

def get_lab3_client_factory():
    return StackingProtocolFactory(lambda: PLSPClient(), lambda: PEEPClient())