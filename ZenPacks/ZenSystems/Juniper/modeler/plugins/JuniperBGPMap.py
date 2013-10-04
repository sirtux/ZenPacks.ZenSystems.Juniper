##########################################################################
# Author:               Jane Curry,  jane.curry@skills-1st.co.uk
# Date:                 February 28th, 2011
# Revised:		Extra debugging added Aug 23, 2011
#
# JuniperBGP modeler plugin
#
# This program can be used under the GNU General Public License version 2
# You can find full information here: http://www.zenoss.com/oss
#
##########################################################################

__doc__ = """JuniperBGPMap

Gather table information from Juniper BGP tables
"""

import re,ipaddr
from Products.DataCollector.plugins.CollectorPlugin import SnmpPlugin, GetMap, GetTableMap

class JuniperBGPMap(SnmpPlugin):
    """Map Juniper BGP table to model."""
    maptype = "JuniperBGPMap"
    modname = "ZenPacks.ZenSystems.Juniper.JuniperBGP"
    relname = "JuniperBG"
    compname = ""

    snmpGetTableMaps = (
        GetTableMap('jnxBgpM2PeerTable',
                    '.1.3.6.1.4.1.2636.5.1.1.2',
#                    '.1.3.6.1.2.1.15.3.1',
                    {
                        '.1.1.1.2':  'bgpStateInt',
                        '.1.1.1.7':  'bgpLocalAddress',
                        '.1.1.1.11':  'bgpRemoteAddress',
                        '.1.1.1.13':  'bgpRemoteASN',
                        '.4.1.1.1': 'bgpLastUpDown',
			'.1.1.1.14': 'jnxBgpM2PeerIndex',
                    }
        ),
    )

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        getdata, tabledata = results
        rm = self.relMap()
        bgpTable = tabledata.get('jnxBgpM2PeerTable')

# If no data supplied then simply return
        if not bgpTable:
            log.warn( 'No SNMP response from %s for the %s plugin', device.id, self.name() )
            log.warn( "Data= %s", tabledata )
            return
 
        for oid, data in bgpTable.items():
            try:
                om = self.objectMap(data)
                if (om.bgpStateInt < 1 or om.bgpStateInt > 6):
                    om.bgpStateInt = 0
                om.bgpStateText = self.operatingStateLookup[om.bgpStateInt]
                om.bgpLastUpDown = om.bgpLastUpDown / 60 / 60 / 24
                om.snmpindex = oid.strip('.')
		om.bgpLocalAddress = self.hexToIp(om.bgpLocalAddress)
		om.bgpRemoteAddress = self.hexToIp(om.bgpRemoteAddress)
                tempname = om.bgpLocalAddress.replace(' ','_')
                tempname = tempname.replace('.','_')
		om.id = self.prepId(om.snmpindex)
		om.snmpindex = om.jnxBgpM2PeerIndex
                #om.id = self.prepId( tempname + '_' + str( om.snmpindex.replace('.','_') ) )
            except (KeyError, IndexError, AttributeError, TypeError), errorInfo:
                log.warn( ' Error in %s modeler plugin %s' % ( self.name(), errorInfo))
                continue
            rm.append(om)
#            log.info('rm %s' % (rm) )

        return rm

    def hexToIp(self,hexAddr):
        ipAddr=[]
        #hexAddrList = hexAddr.split(' ')
        if len(hexAddr)==4:
		for i in hexAddr:
	    		ipAddr.append(str(ord(i)))
            		#ipAddr.append(str(int(i,16)))
        	return '.'.join(ipAddr)
	else:
		for i in hexAddr:
                        ipAddr.append(str(hex(int(str(ord(i))))))
		v6Addr = ""
		colon = False
		position = 0
		for byte in ipAddr:
			position = position + 1
			byte = byte.replace("0x","")
			if len(byte)==1:
				byte="0"+byte
			v6Addr = v6Addr + byte
			if colon == False:
				colon = True
			else:
				colon = False
				if position < 15:
					v6Addr = v6Addr + ":"
			
		ip = ipaddr.IPv6Address(v6Addr)
                return str(ip)

    def binaryToIp(self, binAddr):
        ipAddr = []
        for i in binAddr:
            ipAddr.append(str(ord(i)))
        return '.'.join(ipAddr)

    operatingStateLookup = { 0: 'Unknown',
                             1: 'Idle',
                             2: 'Connect',
                             3: 'Active',
                             4: 'OpenSent',
                             5: 'OpenConfirm',
                             6: 'Established',
                           }

