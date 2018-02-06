"""
  Omnik Solar interface.
  
  This component can retrieve data from the inverter or the Omnik portal.
  If combined the component first tries to retrieve the data from the inverter.
  When the inverter is powered off the missing data is retrieved from the Omnik portal.
  
  For more information: https://github.com/heinoldenhuis/home_assistant_omnik_solar/
  
  Information used and inspiration from source:
  https://github.com/KoenZomers/OmnikApi
  https://github.com/Woutrrr/Omnik-Data-Logger
"""

import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ( EVENT_HOMEASSISTANT_STOP, CONF_SCAN_INTERVAL )
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity
from urllib.request import urlopen
from xml.etree import ElementTree as etree

import binascii
import hashlib
import socket
import struct
import sys

BASE_URL = 'http://{0}:{1}{2}'

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT_INVERTER = 8899
DEFAULT_PORT_PORTAL = 10000
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

CONF_DATASOURCE = 'datasource'
CONF_INVERTER_HOST = 'inverter_host'
CONF_INVERTER_PORT = 'inverter_port'
CONF_INVERTER_SERIAL = 'inverter_serial'
CONF_PORTAL_HOST = 'portal_host'
CONF_PORTAL_PORT = 'portal_port'
CONF_PORTAL_USERNAME = 'portal_username'
CONF_PORTAL_PASSWORD = 'portal_password'
CONF_SENSORS = 'sensors'

DATASOURCE_TYPES = {
    'inverter_and_portal',
    'inverter',
    'portal'
  }

SENSOR_PREFIX = 'Omnik '
SENSOR_TYPES = {
    'actualpower':       ['Actual Power', 'W', 'mdi:weather-sunny'],
    'energytoday':       ['Energy Today', 'kWh', 'mdi:flash-outline'],
    'energytotal':       ['Energy Total', 'kWh', 'mdi:flash-outline'],
    'hourstotal':        ['Hours Total', 'Hours', 'mdi:timer'],
    'invertersn':        ['Inverter Serial Number', None, 'mdi:information-outline'],
    'temperature':       ['Temperature', '°C', 'mdi:thermometer'],
    'dcinputvoltage':    ['DC Input Voltage', 'V', 'mdi:flash-outline'],
    'dcinputcurrent':    ['DC Input Current', 'A', 'mdi:flash-outline'],
    'acoutputvoltage':   ['AC Output Voltage', 'V', 'mdi:flash-outline'],
    'acoutputcurrent':   ['AC Output Current', 'A', 'mdi:flash-outline'],
    'acoutputfrequency': ['AC Output Frequency', 'Hz', 'mdi:flash-outline'],
    'acoutputpower':     ['AC Output Power', 'W', 'mdi:flash-outline'],
    'incometoday':       ['Income Today', 'EUR', 'mdi:currency-eur'],
    'incometotal':       ['Income Total', 'EUR', 'mdi:currency-eur'],
  }

def _check_config_schema(conf):
  """ Check if the data source is valid. """
  datasource = conf[CONF_DATASOURCE]
  if(datasource not in DATASOURCE_TYPES):
    raise vol.Invalid('datasource {} is not valid'.format(datasource))
  
  """ Check if the sensors and attributes are valid. """
  for sensor, attrs in conf[CONF_SENSORS].items():
    if(sensor not in SENSOR_TYPES):
      raise vol.Invalid('sensor {} does not exist'.format(sensor))
    for attr in attrs:
      if(attr not in SENSOR_TYPES):
        raise vol.Invalid('attribute sensor {} does not exist [{}]'.format(attr, sensor))
  
  return conf

PLATFORM_SCHEMA = vol.All(PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DATASOURCE): cv.string,
    vol.Optional(CONF_INVERTER_HOST, default=None): cv.string,
    vol.Optional(CONF_INVERTER_PORT, default=DEFAULT_PORT_INVERTER): cv.positive_int,
    vol.Optional(CONF_INVERTER_SERIAL, default=None): cv.positive_int,
    vol.Optional(CONF_PORTAL_HOST, default=None): cv.string,
    vol.Optional(CONF_PORTAL_PORT, default=DEFAULT_PORT_PORTAL): cv.positive_int,
    vol.Optional(CONF_PORTAL_USERNAME, default=None): cv.string,
    vol.Optional(CONF_PORTAL_PASSWORD, default=None): cv.string,
    vol.Required(CONF_SENSORS): vol.Schema({cv.slug: cv.ensure_list}),
}, extra=vol.PREVENT_EXTRA), _check_config_schema)

def setup_platform(hass, config, add_devices, discovery_info=None):
  """ Set up Omnik sensor. """
  datasource = config.get(CONF_DATASOURCE)
  inverter_host = config.get(CONF_INVERTER_HOST)
  inverter_port = config.get(CONF_INVERTER_PORT)
  inverter_sn = config.get(CONF_INVERTER_SERIAL)
  portal_host = config.get(CONF_PORTAL_HOST)
  portal_port = config.get(CONF_PORTAL_PORT)
  portal_user = config.get(CONF_PORTAL_USERNAME)
  portal_pass = config.get(CONF_PORTAL_PASSWORD)
  
  """ Check input configuration. """
  if(datasource == 'inverter_and_portal') or (datasource == 'inverter'):
    if(inverter_host == None):
      raise vol.Invalid('configuration parameter [inverter_host] does not have a value')
    if(inverter_sn == None):
      raise vol.Invalid('configuration parameter [inverter_serial] does not have a value')
  
  if (datasource == 'inverter_and_portal') or (datasource == 'portal'):
    if(portal_host == None):
      raise vol.Invalid('configuration parameter [portal_host] does not have a value')
    if(portal_user == None):
      raise vol.Invalid('configuration parameter [portal_username] does not have a value')
    if(portal_pass == None):
      raise vol.Invalid('configuration parameter [portal_password] does not have a value')
  
  """ Determine for which sensors data should be retrieved. """
  used_sensors = []
  for type, subtypes in config[CONF_SENSORS].items():
    used_sensors.append(type)
    used_sensors.extend(subtypes)
    
  """ Initialize the Omnik data interface. """
  data = OmnikData(datasource, inverter_host, inverter_port, inverter_sn, portal_host, portal_port, portal_user, portal_pass, used_sensors)
  
  """ Prepare the sensor entities. """
  hass_sensors = []
  for type, subtypes in config[CONF_SENSORS].items():
    hass_sensors.append(OmnikSensor(data, type, subtypes))
  
  add_devices(hass_sensors)

class OmnikSensor(Entity):
  """ Representation of a Omnik sensor. """
  
  def __init__(self, data, type, subtypes):
    """Initialize the sensor."""
    self._data = data
    self._type = type
    self._subtypes = subtypes
    self.p_icon = SENSOR_TYPES[self._type][2]
    self.p_name = SENSOR_PREFIX + SENSOR_TYPES[self._type][0]
    self.p_state = None
    self.p_subtypes = {SENSOR_TYPES[subtype][0]: '{}'.format('unknown') for subtype in subtypes}
    self.p_uom = SENSOR_TYPES[self._type][1]
  
  @property
  def device_state_attributes(self):
    """ Return the state attributes of the sensor. """
    return self.p_subtypes
  
  @property
  def icon(self):
    """ Return the icon of the sensor. """
    return self.p_icon
  
  @property
  def name(self):
    """ Return the name of the sensor. """
    return self.p_name
  
  @property
  def unit_of_measurement(self):
    """ Return the unit the value is expressed in. """
    uom = self.p_uom
    if(self.p_state is None):
      uom = None
    return uom
  
  @property
  def state(self):
    """ Return the state of the sensor. """
    return self.p_state
  
  def update(self):
    """ Update this sensor using the data. """
    
    """ Get the latest data and use it to update our sensor state. """
    self._data.update()
    
    """ Retrieve the sensor data from Omnik Data. """
    sensor_data = self._data.get_sensor_data()
    
    """ Update attribute sensor values. """
    for subtype in self._subtypes:
      newval = sensor_data[subtype]
      uom = SENSOR_TYPES[subtype][1]
      if(uom is None):
        subtypeval = '{}'.format(newval)
      else:
        subtypeval = '{} {}'.format(newval, uom)
        
      self.p_subtypes[SENSOR_TYPES[subtype][0]] = subtypeval
    
    """ Update sensor value. """
    new_state = sensor_data[self._type]
    self.p_state = new_state

class OmnikData(object):
  """ Representation of a Omnik data object used for retrieving data values. """
  
  def __init__(self, datasource, inverter_host, inverter_port, inverter_sn, portal_host, portal_port, portal_user, portal_pass, sensors):
    """ Initialize Omnik data component. """
    self._datasource = datasource
    self._inverter_host = inverter_host
    self._inverter_port = inverter_port
    self._inverter_sn = inverter_sn
    self._portal_host = portal_host
    self._portal_port = portal_port
    self._portal_user =  portal_user
    self._portal_pass = portal_pass
    self._sensors = sensors
    self.interface_inverter = None
    self.interface_portal = None
    self.sensor_data = {type: None for type in list(self._sensors)}
    
    if(self._datasource == 'inverter_and_portal') or (self._datasource == 'inverter'):
      self.interface_inverter = OmnikInverter(self._inverter_host, self._inverter_port, self._inverter_sn)
    
    if (self._datasource == 'inverter_and_portal') or (self._datasource == 'portal'):
      self.interface_portal = OmnikPortal(self._portal_host, self._portal_port, self._portal_user, self._portal_pass) 
  
  def get_sensor_data(self):
    """ Return an array with the sensors and their values. """
    return self.sensor_data
  
  def get_statistics(self):
    """ Gets the statistics from the inverter or portal. """
    if(self.interface_inverter is not None):
      self.interface_inverter.get_statistics()
    
    if (self.interface_portal is not None):
      self.interface_portal.get_statistics()
  
  def read_sensor(self, sensor_type):
    """ Gets the data values from the sensors. """
    value = None
    
    """ Check if the inverter is operational. """
    inverter_enabled = False
    read_inverter = False
    if(self.interface_inverter is not None):
      read_inverter = True
      check = self.interface_inverter.get_temperature()
      if(check is not None):
        inverter_enabled = True
    
    """ Check if the portal is operational. """
    read_portal = False
    if(self.interface_portal is not None):
      read_portal = True
    
    #_LOGGER.warn('read_sensor: inverter enabled %s, inverter read %s, read portal %s', inverter_enabled, read_inverter, read_portal)
    
    """ Retrieve value. """
    if(sensor_type == 'actualpower'):
      if((read_inverter == True) and (inverter_enabled == True)):
        value = self.interface_inverter.get_actualpower()
      elif((read_portal == True)):
        value = self.interface_portal.get_actualpower()
    elif(sensor_type == 'energytoday'):
      if((read_inverter == True) and (inverter_enabled == True)):
        value = self.interface_inverter.get_energytoday()
      elif((read_portal == True)):
        value = self.interface_portal.get_energytoday()
    elif(sensor_type == 'energytotal'):
      if(read_inverter == True):
        value = self.interface_inverter.get_energytotal()
      elif((read_portal == True)):
        value = self.interface_portal.get_energytotal()
    elif sensor_type == 'hourstotal':
      if(read_inverter == True):
        value = self.interface_inverter.get_hourstotal()
      elif((read_portal == True)):
        value = self.interface_portal.get_hourstotal()
    elif sensor_type == 'invertersn':
      if(read_inverter == True):
        value = self.interface_inverter.get_invertersn()
      elif((read_portal == True)):
        value = self.interface_portal.get_invertersn()
    elif sensor_type == 'temperature':
      if(read_inverter == True):
        value = self.interface_inverter.get_temperature()
      elif((read_portal == True)):
        value = self.interface_portal.get_temperature()
    elif sensor_type == 'dcinputvoltage':
      if(read_inverter == True):
        value = self.interface_inverter.get_dcinputvoltage()
      elif((read_portal == True)):
        value = self.interface_portal.get_dcinputvoltage()
    elif sensor_type == 'dcinputcurrent':
      if(read_inverter == True):
        value = self.interface_inverter.get_dcinputcurrent()
      elif((read_portal == True)):
        value = self.interface_portal.get_dcinputcurrent()
    elif sensor_type == 'acoutputvoltage':
      if(read_inverter == True):
        value = self.interface_inverter.get_acoutputvoltage()
      elif((read_portal == True)):
        value = self.interface_portal.get_acoutputvoltage()
    elif sensor_type == 'acoutputcurrent':
      if(read_inverter == True):
        value = self.interface_inverter.get_acoutputcurrent()
      elif((read_portal == True)):
        value = self.interface_portal.get_acoutputcurrent()
    elif sensor_type == 'acoutputfrequency':
      if(read_inverter == True):
        value = self.interface_inverter.get_acoutputfrequency()
      elif((read_portal == True)):
        value = self.interface_portal.get_acoutputfrequency()
    elif sensor_type == 'acoutputpower':
      if(read_inverter == True):
        value = self.interface_inverter.get_acoutputpower()
      elif((read_portal == True)):
        value = self.interface_portal.get_acoutputpower()
    elif sensor_type == 'incometoday':
      if((read_portal == True)):
        value = self.interface_portal.get_incometoday()
      elif(read_inverter == True):
        value = self.interface_inverter.get_incometoday()
    elif sensor_type == 'incometotal':
      if((read_portal == True)):
        value = self.interface_portal.get_incometotal()
      elif(read_inverter == True):
        value = self.interface_inverter.get_incometotal()
    
    return value
  
  def update_sensor_values(self):
    """ Update the sensor data values. """
    sensor_types_to_query = list(self._sensors)
    for sensor_type in sensor_types_to_query:
      self.sensor_data[sensor_type] = self.read_sensor(sensor_type)
  
  @Throttle(MIN_TIME_BETWEEN_UPDATES)
  def update(self):
    """ Update the data of the sensors. """
    self.get_statistics()
    
    """ Retrieve the data values for the sensors. """
    self.update_sensor_values()

class OmnikInverter():
  """ Class with function for reading data from the Omnik inverter. """
  
  def __init__(self, host, port, serial_number):
    """ Initialize the Omnik inverter object. """
    self._host = host
    self._port = port
    self._serial_number = serial_number
    self.raw_msg = None
  
  @staticmethod
  def generate_request(serial_number):
    """
      Create request string for inverter.
      The request string is build from several parts. The first part is a fixed
      4 char string; the second part is the reversed hex notation of the
      serial number twice; then again a fixed string of two chars; a checksum of
      the double serial number with an offset; and finally a fixed ending char.

      Arguments:
        serial_no (integer): Serial number of the inverter
      Returns:
        string: Information request string for inverter
    """
    
    """ Convert the serial number into a bytes array. """
    serial_hex = '{:x}'.format(serial_number)
    serial_bytes = bytearray.fromhex(serial_hex)
    
    """ Calculate the checksum. """
    checksum = 0
    for x in range(0, 4):
      checksum += serial_bytes[x]
    checksum *= 2
    checksum += 115
    checksum &= 0xff
    
    """ Convert the checksum into a byte. """
    checksum_hex = '{:x}'.format(int(checksum))
    checksum_bytes = bytearray.fromhex(checksum_hex)
    
    """ Construct the message which requests the statistics. """
    request_data = bytearray()
    request_data.append(0x68)
    request_data.append(0x02)
    request_data.append(0x40)
    request_data.append(0x30)
    request_data.append(serial_bytes[3])
    request_data.append(serial_bytes[2])
    request_data.append(serial_bytes[1])
    request_data.append(serial_bytes[0])
    request_data.append(serial_bytes[3])
    request_data.append(serial_bytes[2])
    request_data.append(serial_bytes[1])
    request_data.append(serial_bytes[0])
    request_data.append(0x01)
    request_data.append(0x00)
    request_data.append(checksum_bytes[0])
    request_data.append(0x16)
    
    return request_data
  
  def get_statistics(self):
    """ Get statistics from the inverter. """
    
    """ Create a socket (SOCK_STREAM means a TCP socket). """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
      """ Connect to server and send data. """
      sock.connect((self._host, self._port))
      sock.sendall(OmnikInverter.generate_request(self._serial_number))
      
      """ Receive data from the server and shut down. """
      self.raw_msg = sock.recv(1024)
      
    except:
      """ Error handling. """
      self.raw_msg = None
      _LOGGER.error('Could not connect to the inverter on %s:%s', self._host, self._port)
    finally:
      sock.close()
    return
  
  def __get_string(self, begin, end):
    """
      Extract string from message.
      
      Args:
        begin (int): starting byte index of string
        end (int): end byte index of string

      Returns:
        str: String in the message from start to end
    """
    
    try:
      value = self.raw_msg[begin:end].decode()
    except:
      value = None
    
    return value
  
  def __get_short(self, begin, divider=10):
    """
      Extract short from message.
      The shorts in the message could actually be a decimal number. This is
      done by storing the number multiplied in the message. So by dividing the
      short the original decimal number can be retrieved.
  
      Args:
        begin (int): index of short in message
        divider (int): divider to change short to float. (Default: 10)
      Returns:
        int or float: Value stored at location `begin`
    """
    try:
      num = struct.unpack('!H', self.raw_msg[begin:begin + 2])[0]
      if num == 65535:
        value = -1
      else:
        value = float(num) / divider
    except:
      value = None
    
    return value
  
  def __get_long(self, begin, divider=10):
    """
      Extract long from message.
      
      The longs in the message could actually be a decimal number. By dividing
      the long, the original decimal number can be extracted.

      Args:
        begin (int): index of long in message
        divider (int): divider to change long to float. (Default : 10)
      Returns:
        int or float: Value stored at location `begin`
    """
    try:
      value =  float(struct.unpack('!I', self.raw_msg[begin:begin + 4])[0]) / divider
    except:
      value = None
    
    return value
  
  def get_actualpower(self):
    """ Gets the actual power output by the inverter in Watt. """
    return self.__get_short(59, 1)  # Don't divide
  
  def get_energytoday(self):
    """ Gets the energy generated by inverter today in kWh. """
    return self.__get_short(69, 100)  # Divide by 100
  
  def get_energytotal(self):
    """ Gets the total energy generated by inverter in kWh. """
    return self.__get_long(71)
  
  def get_hourstotal(self):
    """ Gets the hours the inverter generated electricity. """
    value = self.__get_long(75, 1) # Don't divide
    
    if(value is not None):
      value = int(value)
    
    return value
  
  def get_invertersn(self):
    """ Gets the serial number of the inverter. """
    return self.__get_string(15, 31)

  def get_temperature(self):
    """
      Gets the temperature recorded by the inverter.
      
      If the temperature is higher then 6500 the inverter power is turned off
      and no temperature is measured.
    """
    value = self.__get_short(31)
    
    if (value is not None):
      if(value > 150):
        value = None
    
    return value
  
  def get_dcinputvoltage(self, i=1):
    """
      Gets the voltage of inverter DC input channel.
      
      Available channels are 1, 2 or 3; if not in this range the function will
      default to channel 1.
      
      Args:
        i (int): input channel (valid values: 1, 2, 3)
      Returns:
        float: PV voltage of channel i
    """
    if i not in range(1, 4):
      i = 1
    num = 33 + (i - 1) * 2
    
    return self.__get_short(num)
  
  def get_dcinputcurrent(self, i=1):
    """
      Gets the current of inverter DC input channel.
      
      Available channels are 1, 2 or 3; if not in this range the function will
      default to channel 1.
      Args:
        i (int): input channel (valid values: 1, 2, 3)
      Returns:
        float: PV current of channel i
    """
    if i not in range(1, 4):
      i = 1
    num = 39 + (i - 1) * 2
    
    return self.__get_short(num)
  
  def get_acoutputvoltage(self, i=1):
    """
      Gets the Voltage of the inverter AC output channel.
      
      Available channels are 1, 2 or 3; if not in this range the function will
      default to channel 1.
      
      Args:
        i (int): output channel (valid values: 1, 2, 3)
      
      Returns:
        float: AC voltage of channel i
    """
    if i not in range(1, 4):
      i = 1
    num = 51 + (i - 1) * 2
    
    return self.__get_short(num)
  
  def get_acoutputcurrent(self, i=1):
    """
      Gets the current of the inverter AC output channel.
      
      Available channels are 1, 2 or 3; if not in this range the function will
      default to channel 1.
      
      Args:
        i (int): output channel (valid values: 1, 2, 3)
      
      Returns:
        float: AC current of channel i
    """
    if i not in range(1, 4):
      i = 1
    num = 45 + (i - 1) * 2
    
    return self.__get_short(num)
  
  def get_acoutputfrequency(self, i=1):
    """
      Gets the frequency of the inverter AC output channel.
      
      Available channels are 1, 2 or 3; if not in this range the function will
      default to channel 1.
      
      Args:
        i (int): output channel (valid values: 1, 2, 3)
      
      Returns:
        float: AC frequency of channel i
    """
    if i not in range(1, 4):
      i = 1
    num = 57 + (i - 1) * 4
    
    return self.__get_short(num, 100)
  
  def get_acoutputpower(self, i=1):
    """
      Gets the power output of the inverter AC output channel.
      
      Available channels are 1, 2 or 3; if no tin this range the function will
      default to channel 1.
      
      Args:
        i (int): output channel (valid values: 1, 2, 3)
      
      Returns:
        float: Power output of channel i
    """
    if i not in range(1, 4):
      i = 1
    num = 59 + (i - 1) * 4
    value = self.__get_short(num, 1) # Don't divide
    
    if(value is not None):
      value = int(value)
    
    return value
  
  def get_incometoday(self):
    """ Gets the income for today. """
    return None
  
  def get_incometotal(self):
    """ Gets the total income. """
    return None

class OmnikPortal():
  """ Class with function for reading data from the Omnik portal. """
  
  def __init__(self, host, port, username, password):
    """ Initialize the Omnik portal object. """
    self._host = host
    self._port = port
    self._username = username
    self._password = password
    self.token = None
    self.station_id = None
    self.data = None
  
  def get_token(self, host, port, username, password):
    """ Gets authorisation token from the portal. """
    token = None
    
    """ Generate the MD5 hash for the password. """
    mdhash = hashlib.md5()
    mdhash.update(password.encode('utf-8'))
    pwhash = mdhash.hexdigest()
    
    """ Get token. """
    try:
      requesturl = BASE_URL.format(host, port, '/serverapi/?method=Login&username=' + username + '&password=' + pwhash + '&key=apitest&client=iPhone')
      root = etree.parse(urlopen(requesturl)).getroot()
      token = root.find('token').text
    except:
      token = None
    
    return token

  def get_station_id(self, host, port, username, token):
    """ Gets the station id for your inverter. """
    station_id = None
    
    """ Get (only first) station. """
    try:
      stationlisturl = BASE_URL.format(host, port, '/serverapi/?method=Powerstationslist&username=' + username + '&token=' + token + '&key=apitest')
      stationroot = etree.parse(urlopen(stationlisturl)).getroot()
      for elem in stationroot.findall('power'):
        station_id = elem.find('stationID').text
    except:
      station_id = None
    
    return station_id
  
  def get_statistics(self):
    """ Get statistics from the portal. """
    
    if(self.token is None):
      self.token = self.get_token(self._host, self._port, self._username, self._password)
    if((self.station_id is None) and (self.token is not None)):
      self.station_id = self.get_station_id(self._host, self._port, self._username, self.token)
    
    if((self.station_id is not None) and (self.token is not None)):
      """Update the data from the portal."""
      try:
        dataurl = BASE_URL.format(self._host, self._port, '/serverapi/?method=Data&username=' + self._username + '&stationid=' + str(self.station_id) + '&token=' + self.token + '&key=apitest')
        self.data = etree.parse(urlopen(dataurl)).getroot()
      except:
        self.data = None
  
  def get_actualpower(self):
    """ Gets the actual power output by the inverter in Watt. """
    value = None
    try:
      income = self.data.find('income')
      value = income.find('ActualPower').text
    except:
      value = None
    
    return value
  
  def get_energytoday(self):
    """ Gets the energy generated by inverter today in kWh. """
    value = None
    try:
      income = self.data.find('income')
      value = income.find('etoday').text
    except:
      value = None
    
    return value
  
  def get_energytotal(self):
    """ Gets the total energy generated by inverter in kWh. """
    value = None
    try:
      income = self.data.find('income')
      value = income.find('etotal').text
    except:
      value = None
    
    return value
  
  def get_hourstotal(self):
    """ Not supported by the portal. """
    return None
  
  def get_invertersn(self):
    """ Not supported by the portal. """
    return None

  def get_temperature(self):
    """ Not supported by the portal. """
    return None
  
  def get_dcinputvoltage(self, i=1):
    """ Not supported by the portal. """
    return None
  
  def get_dcinputcurrent(self, i=1):
    """ Not supported by the portal. """
    return None
  
  def get_acoutputvoltage(self, i=1):
    """ Not supported by the portal. """
    return None
  
  def get_acoutputcurrent(self, i=1):
    """ Not supported by the portal. """
    return None
  
  def get_acoutputfrequency(self, i=1):
    """ Not supported by the portal. """
    return None
  
  def get_acoutputpower(self, i=1):
    """ Not supported by the portal. """
    return None
  
  def get_incometoday(self):
    """ Gets the income for today. """
    value = None
    try:
      income = self.data.find('income')
      value = income.find('TodayIncome').text
    except:
      value = None
    
    return value
  
  def get_incometotal(self):
    """ Gets the total income. """
    value = None
    try:
      income = self.data.find('income')
      value = income.find('TotalIncome').text
    except:
      value = None
    
    return value
