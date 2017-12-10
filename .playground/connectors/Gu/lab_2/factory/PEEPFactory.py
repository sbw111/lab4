from playground.network.common import StackingProtocolFactory
from ..protocols import PEEPServer, PEEPClient, PassThroughProtocol


def get_lab2_server_factory():
    return StackingProtocolFactory(lambda: PassThroughProtocol(), lambda: PEEPServer())


def get_lab2_client_factory():
    return StackingProtocolFactory(lambda: PassThroughProtocol(), lambda: PEEPClient())