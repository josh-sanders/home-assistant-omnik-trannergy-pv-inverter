# Home Assistant Omnik/Trannergy PV Inverter custom component

The Omnik/Trannergy PV Inverter custom component will retrieve data from an Omnik or Trannergy PV inverter.
The values will be presented as sensors (or attributes of sensors) in [Home Assistant](https://home-assistant.io/).

![Home Assistant dashboard showing Omnik/Trannergy PV Inverter custom compnent](https://raw.githubusercontent.com/josh-sanders/home-assistant-omnik-trannergy-pv-inverter/master/images/omnik_sensor_ui.png)

> ❤️ This is a continuation of the archived work of: https://github.com/heinoldenhuis/home_assistant_omnik_solar and https://github.com/hultenvp/home_assistant_omnik_solar.

> ⚠️  Your PV inverter must support http calls which is used to retrieve data responses.

## HACS (Home Assistant Community Store)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=josh-sanders&repository=home-assistant-omnik-trannergy-pv-inverter&category=integration)

This is a custom component. Custom components are not installed by default in your Home Assistant installation.
[HACS](https://custom-components.github.io/hacs/) is an Home Assistant store integration from which this integration can be easily installed and updated.
By using HACS you will also make sure that any new versions are installed by default and as simple as the installation itself.

## Manual installation

Create a directory called `omnik` in the `<config directory>/custom_components/` directory on your Home Assistant instance.
Install this component by copying the files in [`/custom_components/omnik/`]:

* [`__init__.py`](https://raw.githubusercontent.com/josh-sanders/home-assistant-omnik-trannergy-pv-inverter/master/custom_components/omnik/__init__.py),
* [`manifest.json`](https://raw.githubusercontent.com/josh-sanders/home-assistant-omnik-trannergy-pv-inverter/master/custom_components/omnik/manifest.json), and
* [`sensor.py`](https://raw.githubusercontent.com/josh-sanders/home-assistant-omnik-trannergy-pv-inverter/master/custom_components/omnik/sensor.py)

from this repo into the new `<config directory>/custom_components/omnik/` directory you just created.

This is how your custom_components directory should be:

```bash
custom_components
├── omnik
│   ├── __init__.py
│   ├── manifest.json
│   └── sensor.py
```

## Configuration example

To enable this sensor, add the following lines to your configuration.yaml file:

``` YAML
sensor:
  - platform: omnik
    name: MyOmnik
    inverter_host: 192.168.1.123
    inverter_port: 8899
    inverter_serial: <serial number wifi/lan module> (example 1612345603)
    scan_interval: 60
    sensors:
      actualpower: [energytotal, energytoday]
      energytoday:
      energytotal:
      hourstotal:
      invertersn:
      temperature:
      dcinputvoltage1:
      dcinputcurrent1:
      dcinputvoltage2:
      dcinputcurrent2:
      acoutputvoltage1:
      acoutputcurrent1:
      acoutputfrequency1:
      acoutputpower1:
```

Configuration variables:

* **inverter_host** (Required): The IP address of the Omnik solar inverter.
* **inverter_port** (Optional): The port nummber of the Omnik solar inverter. Default port 8899 is used.
* **inverter_serial** (Required): The device serial number of the Omnik solar wifi/lan module.
* **name** (Optional): Let you overwrite the name of the device in the frontend. *Default value: Omnik*
* **sensors** (Required): List of values which will be presented as sensors:
  * *actualpower*: Sensor with the actual power value.
  * *energytoday*: Sensor with the total energy value for the current day.
  * *energytotal*: Sensor with the total energy value.
  * *hourstotal*: Sensor with the total hours value.
  * *invertersn*: Sensor with the serial number value.
  * *temperature*: Sensor with the temperature value for the inverter.
  * *dcinputvoltage*: Sensor with the actual DC input voltage value.
  * *dcinputcurrent*: Sensor with the actual DC input current value.
  * *acoutputvoltage*: Sensor with the actual AC output voltage value.
  * *acoutputcurrent*: Sensor with the actual AC output current value.
  * *acoutputfrequency*: Sensor with the actual AC output frequenty value.
  * *acoutputpower*: Sensor with the actual AC output power value.

You can create composite sensors, where the subsensors will be shown as attributes of the main sensor, for example:

``` YAML
    sensors:
      actualpower: [energytotal, energytoday]
```

## Thanks 🌞

Big thanks to:

* [@heinoldenhuis](https://github.com/heinoldenhuis) for the original integration.
* [@hultenvp](https://github.com/hultenvp) for previously maintaining this HACS custom component.

## Similar Projects

If this custom component is not working for you, please try these similar projects:

* [Omnik Inverter Integration for Home Assistant](https://github.com/robbinjanssen/home-assistant-omnik-inverter)
* [Home Assistant custom component for SolarMAN (IGEN Tech) solar inverter logger](https://github.com/KodeCR/home-assistant-solarman)
