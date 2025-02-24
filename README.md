# Home Assistant Omnik/Trannergy PV Inverter custom component

The Omnik/Trannergy PV Inverter custom component uses local polling to retrieve data from an Omnik or Trannergy PV inverter.
The values will be presented as sensors (or attributes of sensors) in [Home Assistant](https://home-assistant.io/).

> ❤️ This integration is a continuation of [hultenvp/home_assistant_omnik_solar](https://github.com/hultenvp/home_assistant_omnik_solar), which is now archived.

![Home Assistant dashboard showing Omnik/Trannergy PV Inverter custom compnent](https://raw.githubusercontent.com/josh-sanders/home-assistant-omnik-trannergy-pv-inverter/master/images/omnik_sensor_ui.png)

## Supported inverters

I have tested this integration with a Trannergy SGN5400TL that has a wifi kit with serial number starting with 645xxxxxx.

Please comment on your experience with this integration in the [github discussion](https://github.com/josh-sanders/home-assistant-omnik-trannergy-pv-inverter/discussions/3).

## Installation

TL;DR click here: [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=josh-sanders&repository=home-assistant-omnik-trannergy-pv-inverter&category=integration)

### HACS installation

#### Search or browse the store

🚀 Coming soon!
I've submitted a [pull request](https://github.com/hacs/default/pull/2627) to have this integration published to HACS, until it's merged please add it as a custom repository.

#### Custom repository

1. Open the HACS dashboard by clicking on HACS in the lefthand menu of Home Assistant
2. Click on the 3 dots in the top right corner
3. Select "Custom repositories"
4. Add the URL to this repository: <https://github.com/josh-sanders/home-assistant-omnik-trannergy-pv-inverter/>
5. Select "Integration" 
6. Click the "ADD" button

#### About HACS

The [Home Assistant Community Store (HACS)](https://hacs.xyz/) is a custom integration that provides a UI to manage custom elements in Home Assistant. HACS is a custom component and is not installed by default in your Home Assistant installation. By using HACS you will also make sure that any new versions are installed by default and as simple as the installation itself.

### Manual installation

Create a directory called `omnik` in the `<config directory>/custom_components/` directory on your Home Assistant instance.
Install this component by copying the files in [`/custom_components/omnik/`]:

* [`__init__.py`](https://raw.githubusercontent.com/josh-sanders/home-assistant-omnik-trannergy-pv-inverter/master/custom_components/omnik/__init__.py),
* [`manifest.json`](https://raw.githubusercontent.com/josh-sanders/home-assistant-omnik-trannergy-pv-inverter/master/custom_components/omnik/manifest.json), and
* [`sensor.py`](https://raw.githubusercontent.com/josh-sanders/home-assistant-omnik-trannergy-pv-inverter/master/custom_components/omnik/sensor.py)

from this repo into the new `<config directory>/custom_components/omnik/` directory you just created.

This is how your `custom_components/` directory should be:

``` bash
custom_components
├── omnik
│   ├── __init__.py
│   ├── manifest.json
│   └── sensor.py
```

## Configuration

After you've completed installation, you need to edit Home Assistants' [`configuration.yaml`](https://www.home-assistant.io/docs/configuration/) file. This file contains integrations to be loaded along with their configurations. Throughout the documentation, you will find snippets that you can add to your configuration file to enable specific functionality.

The following example has everything you need to get started, just change the values for your inverter's serial number and host IPv4 address:

``` YAML
sensor:
  - platform: omnik
    inverter_serial: <serial number wifi/lan module> (example 1612345603)
    inverter_host: 192.168.1.123
    inverter_port: 8899
    name: MyOmnik
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

### Configuration variables

* **`inverter_serial`** (Required): The device serial number of the PV inverter's wifi/lan module.
* **`inverter_host`** (Required): The IP address of the PV inverter.
* **`inverter_port`** (Optional): The port nummber of the PV inverter. Default port 8899 is used.
* **`name`** (Optional): Let you overwrite the name of the device in the frontend. *Default value: Omnik*
* **`scan_interval`** (Optional): The inverter will be polled at an interval specified in seconds.
* **`sensors`** (Required): List of values which will be presented as sensors:
  * *`actualpower`*: Sensor with the actual power value.
  * *`energytoday`*: Sensor with the total energy value for the current day.
  * *`energytotal`*: Sensor with the total energy value.
  * *`hourstotal`*: Sensor with the total hours value.
  * *`invertersn`*: Sensor with the serial number value.
  * *`temperature`*: Sensor with the temperature value for the inverter.
  * *`dcinputvoltage`*: Sensor with the actual DC input voltage value.
  * *`dcinputcurrent`*: Sensor with the actual DC input current value.
  * *`acoutputvoltage`*: Sensor with the actual AC output voltage value.
  * *`acoutputcurrent`*: Sensor with the actual AC output current value.
  * *`acoutputfrequency`*: Sensor with the actual AC output frequenty value.
  * *`acoutputpower`*: Sensor with the actual AC output power value.

The `dcinput` and `acoutput` sensors can be configured for up to 3 channels, for example:

``` YAML
      dcinputvoltage1:   
      dcinputcurrent1:   
      dcinputvoltage2:   
      dcinputcurrent2:   
      dcinputvoltage3:   
      dcinputcurrent3:   
      acoutputvoltage1:  
      acoutputcurrent1:  
      acoutputfrequency1:
      acoutputpower1:    
      acoutputvoltage2:  
      acoutputcurrent2:  
      acoutputfrequency2:
      acoutputpower2:    
      acoutputvoltage3:  
      acoutputcurrent3:  
      acoutputfrequency3:
      acoutputpower3:    
```

You can create composite sensors, where the subsensors will be shown as attributes of the main sensor, for example:

``` YAML
      actualpower: [energytotal, energytoday]
```

## Thanks 🌞

Big thanks to:

* [@heinoldenhuis](https://github.com/heinoldenhuis) for the original integration.
* [@hultenvp](https://github.com/hultenvp) for previously maintaining this HACS custom component.

## Similar Projects

If this custom component is not working for you, please try these similar projects:

* [KoenZomers/OmnikApi](https://github.com/KoenZomers/OmnikApi): Omnik Solar API in C#
* [Woutrrr/Omnik-Data-Logger](https://github.com/Woutrrr/Omnik-Data-Logger): Data logger for Omnik Solar Inverters
* [robbinjanssen/home-assistant-omnik-inverter](https://github.com/robbinjanssen/home-assistant-omnik-inverter): Omnik Inverter Integration for Home Assistant
* [KodeCR/home-assistant-solarman](https://github.com/KodeCR/home-assistant-solarman): Home Assistant custom component for SolarMAN (IGEN Tech) solar inverter logger
* [XtheOne/Inverter-Data-Logger](https://github.com/XtheOne/Inverter-Data-Logger):Data logger for Omnik/Hosola and other Solarman Wi-Fi kit powered Solar Inverters
* [davidrapan/ha-solarman](https://github.com/davidrapan/ha-solarman): ⚡ Solarman Stick Logger integration for 🏡 Home Assistant
