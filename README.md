# Home Assistant Omnik solar sensor component
The Omnik soloar sensor component will poll a Omnik solar inverter and/or extract values from the [Omnik Portal](https://www.omnikportal.com/). The values will be presented as sensors (or attributes of sensors) in [Home Assistant](https://home-assistant.io/).

With the datasource option the user can choose to only retrieve data from the Omnik solar inverter or the Omnik portal, or the user can choose to retrieve the data from both datasources.
> Note: When data is retrieved from both datasources the available Omnik solar inverter values are used first. When the Omnik solar inverter is powered off the missing values are retrieved from the Omnik portal.

### Installation:

Copy the omnik.py file and place it in <config_dir>/custom_components/sensor/omnik.py.

To enable this sensor, add the following lines to your configuration.yaml file:

``` YAML
sensor:
  - platform: omnik
    datasource: inverter_and_portal
    inverter_host: <ip address inverter>
    inverter_port: <port inverter>
    inverter_serial: <serial number inverter> (example 1234567603)
    portal_host: www.omnikportal.com
    portal_port: 10000
    portal_username: <username omnik portal>
    portal_password: <password omnik portal>
    scan_interval: 60
    sensors:
      actualpower: [energytotal, energytoday]
      energytoday:
      energytotal:
      hourstotal:
      invertersn:
      temperature:
      dcinputvoltage:
      dcinputcurrent:
      acoutputvoltage:
      acoutputcurrent:
      acoutputfrequency:
      acoutputpower:
      incometoday:
      incometotal:
```

Configuration variables:

* **datasource** (Required): The datasource used, which can be either *inverter_and_portal*, *inverter* or *portal*.
* **inverter_host** (Optional): The IP address of the Omnik solar inverter.
* **inverter_port** (Optional): The port nummber of the Omnik solar inverter.
* **inverter_serial** (Optional): The serial number of the Omnik solar inverter.
* **portal_host** (Optional): The http(s) host address used for the [Omnik Portal](https://www.omnikportal.com/).
* **portal_port** (Optional): The http(s) port used for the [Omnik Portal](https://www.omnikportal.com/).
* **portal_username** (Optional): The username used for the [Omnik Portal](https://www.omnikportal.com/).
* **portal_password** (Optional): The password used for the [Omnik Portal](https://www.omnikportal.com/).
* **sensors** (Required): List of values which will be presented as sensors:
  * *actualpower*: Sensor with the actual power value (inverter and portal).
  * *energytoday*: Sensor with the total energy value for the current day (inverter and portal).
  * *energytotal*: Sensor with the total energy value (inverter and portal).
  * *hourstotal*: Sensor with the actual power value (inverter).
  * *invertersn*: Sensor with the serial number value (inverter).
  * *temperature*: Sensor with the temperature value for the inverter (inverter).
  * *dcinputvoltage*: Sensor with the actual DC input voltage value (inverter).
  * *dcinputcurrent*: Sensor with the actual DC input current value (inverter).
  * *acoutputvoltage*: Sensor with the actual AC output voltage value (inverter).
  * *acoutputcurrent*: Sensor with the actual AC output current value (inverter).
  * *acoutputfrequency*: Sensor with the actual AC output frequenty value (inverter).
  * *acoutputpower*: Sensor with the actual AC output power value (inverter).
  * *incometoday*: Sensor with the total income for today value (portal).
  * *incometotal*: Sensor with the total income value (portal).

> Note: Not all values could be retrieved from either the inverter or portal. In the case no value could be retrieved the value is unknown, for numbers 0 is returned.

You can create composite sensors, where the subsensors will be shown as attributes of the main sensor, for example:
``` YAML
    sensors:
      actualpower: [energytotal, energytoday]
```
