import bme680
import time
from datetime import datetime, timezone
import uuid
import copy
from gpsdclient import GPSDClient

# Fledge documentation
# http://fledge-iot.readthedocs.io/

# Pimoroni bme680 
# https://learn.pimoroni.com/article/getting-started-with-bme680-breakout

_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'Python module name of the plugin to load',
        'type': 'string',
        'default': 'bme680'
    },
    'gps': {
        'description': 'Check to enable lat/long readings',
        'type': 'boolean',
        'default': 'true'
    },
    'gpsdIPaddress': {
        'description': 'IP of the GPSD server to connect to',
        'type': 'string',
        'default': '192.168.1.1',
        'displayName':'GPSD IP Addresss'
    },
        'gpsdDefaultGateway': {
        'description': 'Enable if GPSD server is the default gateway',
        'type': 'boolean',
        'default': 'false',
        'displayName':'GPSD Default Gateway'
    }

}

_LOGGER = logger.setup(__name__)


def plugin_info():


    return {
        'name': 'bme680',
        'version': '1.0',
        'mode': 'poll',
        'type': 'south',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(config):
    global sensor 
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except (RuntimeError, IOError):
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
    
    #bme680 parameters
    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)
    sensor.set_gas_status(bme680.DISABLE_GAS_MEAS)
    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)
    
    handle = copy.deepcopy(config)
    return handle
    


def plugin_poll(handle):
    global sensor
    lat=0
    lon=0

    #Get GPS readings if configured to do so
    if handle['gps']['value']:
        try:
            if handle['gpsdDefaultGateway']['value']:
                gws = netifaces.gateways()
                gpsIP = gws['default'][netifaces.AF_INET][0]
            else:
                gpsIP=handle['gpsdIPaddress']['value']
            client = GPSDClient(host=gpsIP)
            for result in client.dict_stream(convert_datetime=True):
                if result["class"] == "TPV":
                    lat=result.get("lat", "0")
                    lon=result.get("lon", "0")
                    break
            client.close()
        except:
            pass
    
    #Read bme680
    sensor.get_sensor_data()
    timestamp = str(datetime.now(tz=timezone.utc))

    #Package data and return to fledge
    if handle['gps']['value']:
        readings = {'latitude':lat, 'longitude':lon,'temperature': sensor.data.temperature, 'pressure':sensor.data.pressure,'humidity': sensor.data.humidity, 'gas': sensor.data.gas_resistance}

    else:
        readings = {'temperature': sensor.data.temperature, 'pressure':sensor.data.pressure,'humidity': sensor.data.humidity, 'gas': sensor.data.gas_resistance}
 
    wrapper = {
            'asset':     'bme680',
            'timestamp': timestamp,
            'key':       str(uuid.uuid4()),
            'readings':  readings
    }
    return wrapper  
    


def plugin_reconfigure(handle, new_config):

    new_handle = copy.deepcopy(new_config)  
    return new_handle


def plugin_shutdown(handle):

    pass




