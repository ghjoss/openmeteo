import network
import time
from router import WIFI_SSID, WIFI_PASSWORD

def wifi_connect():
    """
    Connect to the wifi network using the SSID and PASSWORD

    Args:
        none

    Returns:
        The network.WLAN object instantiated
    """
    wlan = network.WLAN(network.WLAN.IF_STA)
    
    # ensure that the network does not have a currently active connection
    wlan.active(False)
    time.sleep(1.0)
    
    # reinitialize
    wlan.active(True)
    #clear any left-overs
    wlan.disconnect()
    time.sleep(1.0)
    
    
    # set performance mode and connect
    #wlan.config(pm=network.WLAN.PM_PERFORMANCE)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    # Wait for the connection to actually establish (30 seconds)
    max_wait = 10
    while max_wait > 0:
        status = wlan.status()
        if status < 0 or status >= 3: # 3 is STAT_GOT_IP
            break
        max_wait -= 1
        time.sleep(1)

    if wlan.status() != network.STAT_GOT_IP:
        return None
    
    return wlan
