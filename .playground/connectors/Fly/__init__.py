from .lab2_protocol import *
import playground

cf = StackingProtocolFactory(lambda: PassThroughc2())
sf = StackingProtocolFactory(lambda: PassThroughs2())


lab_connector = playground.Connector(protocolStack=(cf, sf))
playground.setConnector("Fly_protocol", lab_connector)
