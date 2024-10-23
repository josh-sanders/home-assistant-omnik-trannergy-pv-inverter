"""
  PV Inverter interface.

  This component can retrieve data from an Omnik or Trannergy PV inverter.

  For more information: https://github.com/josh-sanders/home_assistant_omnik_solar/
"""

import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STOP,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

import socket
import struct

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT_INVERTER = 8899
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=1)

CONF_INVERTER_HOST = 'inverter_host'
CONF_INVERTER_PORT = 'inverter_port'
CONF_INVERTER_SERIAL = 'inverter_serial'
CONF_SENSORS = 'sensors'

SENSOR_PREFIX = 'Omnik'
SENSOR_TYPES = {
  'status':             ['Status',                 None,  'mdi:weather-sunny',               None,                          None],
  'actualpower':        ['Actual Power',           'W',   'mdi:solar-power',                 SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT],
  'energytoday':        ['Energy Today',           'kWh', 'mdi:chart-bell-curve-cumulative', SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING],
  'energytotal':        ['Energy Total',           'kWh', 'mdi:meter-electric-outline',      SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING],
  'hourstotal':         ['Hours Total',            'h',   'mdi:timer-outline',               SensorDeviceClass.DURATION,    SensorStateClass.TOTAL_INCREASING],
  'invertersn':         ['Inverter Serial Number', None,  'mdi:information-outline',         None,                          None],
  'temperature':        ['Temperature',            '°C',  'mdi:thermometer',                 SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT],
  'dcinputvoltage1':    ['DC Input Voltage 1',     'V',   'mdi:flash-outline',               SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT],
  'dcinputcurrent1':    ['DC Input Current 1',     'A',   'mdi:current-dc',                  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT],
  'dcinputvoltage2':    ['DC Input Voltage 2',     'V',   'mdi:flash-outline',               SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT],
  'dcinputcurrent2':    ['DC Input Current 2',     'A',   'mdi:current-dc',                  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT],
  'dcinputvoltage3':    ['DC Input Voltage 3',     'V',   'mdi:flash-outline',               SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT],
  'dcinputcurrent3':    ['DC Input Current 3',     'A',   'mdi:current-dc',                  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT],
  'acoutputvoltage1':   ['AC Output Voltage 1',    'V',   'mdi:flash-outline',               SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT],
  'acoutputcurrent1':   ['AC Output Current 1',    'A',   'mdi:current-ac',                  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT],
  'acoutputfrequency1': ['AC Output Frequency 1',  'Hz',  'mdi:sine-wave',                   SensorDeviceClass.FREQUENCY,   SensorStateClass.MEASUREMENT],
  'acoutputpower1':     ['AC Output Power 1',      'W',   'mdi:solar-power',                 SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT],
  'acoutputvoltage2':   ['AC Output Voltage 2',    'V',   'mdi:flash-outline',               SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT],
  'acoutputcurrent2':   ['AC Output Current 2',    'A',   'mdi:current-ac',                  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT],
  'acoutputfrequency2': ['AC Output Frequency 2',  'Hz',  'mdi:sine-wave',                   SensorDeviceClass.FREQUENCY,   SensorStateClass.MEASUREMENT],
  'acoutputpower2':     ['AC Output Power 2',      'W',   'mdi:solar-power',                 SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT],
  'acoutputvoltage3':   ['AC Output Voltage 3',    'V',   'mdi:flash-outline',               SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT],
  'acoutputcurrent3':   ['AC Output Current 3',    'A',   'mdi:current-ac',                  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT],
  'acoutputfrequency3': ['AC Output Frequency 3',  'Hz',  'mdi:sine-wave',                   SensorDeviceClass.FREQUENCY,   SensorStateClass.MEASUREMENT],
  'acoutputpower3':     ['AC Output Power 3',      'W',   'mdi:solar-power',                 SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT],
}

def _check_config_schema(conf):
  """ Check if the sensors and attributes are valid. """
  for sensor, attrs in conf[CONF_SENSORS].items():
    if(sensor not in SENSOR_TYPES):
      raise vol.Invalid('sensor {} does not exist'.format(sensor))
    for attr in attrs:
      if(attr not in SENSOR_TYPES):
        raise vol.Invalid('attribute sensor {} does not exist [{}]'.format(attr, sensor))

  return conf

PLATFORM_SCHEMA = vol.All(PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=SENSOR_PREFIX): cv.string,
    vol.Optional(CONF_INVERTER_HOST, default=None): cv.string,
    vol.Optional(CONF_INVERTER_PORT, default=DEFAULT_PORT_INVERTER): cv.positive_int,
    vol.Optional(CONF_INVERTER_SERIAL, default=None): cv.positive_int,
    vol.Required(CONF_SENSORS): vol.Schema({cv.slug: cv.ensure_list}),
}, extra=vol.PREVENT_EXTRA), _check_config_schema)

def setup_platform(hass, config, add_devices, discovery_info=None):
  """ Set up Omnik sensor. """
  inverter_name = config.get(CONF_NAME)
  inverter_host = config.get(CONF_INVERTER_HOST)
  inverter_port = config.get(CONF_INVERTER_PORT)
  inverter_sn = config.get(CONF_INVERTER_SERIAL)

  """ Check input configuration. """
  if(inverter_host == None):
    raise vol.Invalid('configuration parameter [inverter_host] does not have a value')
  if(inverter_sn == None):
    raise vol.Invalid('configuration parameter [inverter_serial] does not have a value')

  """ Determine for which sensors data should be retrieved. """
  used_sensors = []
  for type, subtypes in config[CONF_SENSORS].items():
    used_sensors.append(type)
    used_sensors.extend(subtypes)

  """ Initialize the Omnik data interface. """
  data = OmnikData(inverter_host, inverter_port, inverter_sn, used_sensors)

  """ Prepare the sensor entities. """
  hass_sensors = []
  for type, subtypes in config[CONF_SENSORS].items():
    hass_sensors.append(OmnikSensor(inverter_name, inverter_sn, data, type, subtypes))

  add_devices(hass_sensors)

class OmnikSensor(SensorEntity):
  """ Representation of an Omnik sensor. """

  def __init__(self, inverter_name, inverter_sn, data, type, subtypes):
    """Initialize the sensor."""
    self._inverter_name = inverter_name
    self._data = data
    self._type = type
    self._subtypes = subtypes

    self.p_subtypes = {SENSOR_TYPES[subtype][0]: '{}'.format('unknown') for subtype in subtypes}

    # Properties
    self._icon = SENSOR_TYPES[self._type][2]
    self._name = self._inverter_name + ' ' + SENSOR_TYPES[self._type][0]
    self._attr_native_value = None
    self._attr_native_unit_of_measurement = SENSOR_TYPES[self._type][1]
    self._attr_device_class = SENSOR_TYPES[self._type][3]
    self._attr_state_class = SENSOR_TYPES[self._type][4]
    self._attr_unique_id = f"{inverter_sn}{self._name}".replace(" ", "_")


  @property
  def should_poll(self):
    """No polling needed."""
    return True

  @property
  def extra_state_attributes(self):
    """Return entity specific state attributes."""
    return self.p_subtypes

  @property
  def icon(self):
    """ Return the icon of the sensor. """
    return self._icon

  @property
  def name(self):
    """ Return the name of the sensor. """
    return self._name

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
    self._attr_native_value = new_state

class OmnikData(object):
  """ Representation of a Omnik data object used for retrieving data values. """

  def __init__(self, inverter_host, inverter_port, inverter_sn, sensors):
    """ Initialize Omnik data component. """
    self._inverter_host = inverter_host
    self._inverter_port = inverter_port
    self._inverter_sn = inverter_sn
    self._sensors = sensors
    self.interface_inverter = OmnikInverter(self._inverter_host, self._inverter_port, self._inverter_sn)
    self.sensor_data = {type: None for type in list(self._sensors)}

  def get_sensor_data(self):
    """ Return an array with the sensors and their values. """
    return self.sensor_data

  def get_statistics(self):
    """ Gets the statistics from the inverter or portal. """
    self.interface_inverter.get_statistics()

  def read_sensor(self, sensor_type):
    """Gets the data values from the sensors."""
    value = None

    """ Check if the inverter is operational. """
    inverter_enabled = False
    check = self.interface_inverter.get_temperature()
    if check is not None:
      inverter_enabled = True

    # TODO: All code below (the way read_sensor is called) needs a refactor.

    def find_and_get_property(t, values):
      for (name, getter) in values.items():
        if t.startswith(name):
          n = t.removeprefix(name)
          return getter(int(n))

    """ Retrieve value. """
    if sensor_type == "status":
      if inverter_enabled == True:
        value = "Online"
      else:
        value = "Offline"
    if sensor_type == "actualpower":
      if inverter_enabled == True:
        value = self.interface_inverter.get_actualpower()
      else:
        value = 0
    elif sensor_type == "energytoday":
      value = self.interface_inverter.get_energytoday()
    elif sensor_type == "energytotal":
      value = self.interface_inverter.get_energytotal()
    elif sensor_type == "hourstotal":
      value = self.interface_inverter.get_hourstotal()
    elif sensor_type == "invertersn":
      value = self.interface_inverter.get_invertersn()
    elif sensor_type == "temperature":
      value = self.interface_inverter.get_temperature()
    elif sensor_type.startswith("dcinput"):
      t = sensor_type.removeprefix("dcinput")
      values = {
        "voltage": self.interface_inverter.get_dcinputvoltage,
        "current": self.interface_inverter.get_dcinputcurrent,
      }
      value = find_and_get_property(t, values)
    elif sensor_type.startswith("acoutput"):
      t = sensor_type.removeprefix("acoutput")
      values = {
        "voltage": self.interface_inverter.get_acoutputvoltage,
        "current": self.interface_inverter.get_acoutputcurrent,
        "frequency": self.interface_inverter.get_acoutputfrequency,
        "power": self.interface_inverter.get_acoutputpower,
      }
      value = find_and_get_property(t, values)

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
    double_hex = hex(serial_number)[2:] * 2
    serial_bytes = bytearray.fromhex(double_hex)
    serial_bytes.reverse()

    cs_count = 115 + sum(serial_bytes)
    checksum = bytearray.fromhex(hex(cs_count)[-2:])

    """ Construct the message which requests the statistics. """
    request_data = bytearray([0x68, 0x02, 0x40, 0x30])
    request_data.extend(serial_bytes)
    request_data.extend([0x01, 0x00])
    request_data.extend(checksum)
    request_data.append(0x16)

    _LOGGER.info('Request: %s', request_data.hex(' '))
    return request_data

  def get_statistics(self):
    """ Get statistics from the inverter. """

    sock = None

    """ Create a socket (SOCK_STREAM means a TCP socket). """
    try:
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
      sock = None

    """ Connect to server. """
    try:
      sock.connect((self._host, self._port))
    except:
      sock.close()
      sock = None

    if sock is None:
      self.raw_msg = None
      _LOGGER.debug('Could not connect to the inverter on %s:%s', self._host, self._port)
      return

    """ Query the server and receive data. """
    with sock:
      sock.sendall(OmnikInverter.generate_request(self._serial_number))
      self.raw_msg = sock.recv(1024)
      _LOGGER.info('Response: %s', self.raw_msg.hex(' '))

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
    value = self.__get_short(59, 1) # Don't divide
    if(value is not None):
      value = int(value)
    _LOGGER.info('get_actualpower: %s', repr(value))
    return value

  def get_energytoday(self):
    """ Gets the energy generated by inverter today in kWh. """
    value = self.__get_short(69, 100) # Divide by 100
    _LOGGER.info('get_energytoday: %s', repr(value))
    return value

  def get_energytotal(self):
    """ Gets the total energy generated by inverter in kWh. """
    value = self.__get_long(71)
    _LOGGER.info('get_energytotal: %s', repr(value))
    return value

  def get_hourstotal(self):
    """ Gets the hours the inverter generated electricity. """
    value = self.__get_long(75, 1) # Don't divide
    if(value is not None):
      value = int(value)
    _LOGGER.info('get_hourstotal: %s', repr(value))
    return value

  def get_invertersn(self):
    """ Gets the serial number of the inverter. """
    value = self.__get_string(15, 31)
    _LOGGER.info('get_invertersn: %s', value)
    return value

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
    _LOGGER.info('get_temperature: %s', repr(value))
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
    value = self.__get_short(num)
    _LOGGER.info('get_dcinputvoltage%d: %s', i, repr(value))
    return value

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
    value = self.__get_short(num)
    _LOGGER.info('get_dcinputcurrent%d: %s', i, repr(value))
    return value

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
    value = self.__get_short(num)
    _LOGGER.info('get_acoutputvoltage%d: %s', i, repr(value))
    return value

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
    value = self.__get_short(num)
    _LOGGER.info('get_acoutputcurrent%d: %s', i, repr(value))
    return value

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
    value = self.__get_short(num, 100)
    _LOGGER.info('get_acoutputfrequency%d: %s', i, repr(value))
    return value

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
    _LOGGER.info('get_acoutputpower%d: %s', i, repr(value))
    return value
