'''
Created on 2017年10月4日

@author: wangweizhou
'''
import playground
from playground.network.common import StackingProtocolFactory
from .TranCliProto import *
from .TranSerProto import *

lab2ClientFactory = StackingProtocolFactory(lambda: TranCliProto())
lab2ServerFactory = StackingProtocolFactory(lambda: TranSerProto())
lab2Connector = playground.Connector(protocolStack=(lab2ClientFactory, lab2ServerFactory))
playground.setConnector("Wang_protocol", lab2Connector)
