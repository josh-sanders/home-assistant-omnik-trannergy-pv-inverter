# Home Assistant Omnik solar sensor component
> Note: This is a continuation of the archived work of https://github.com/heinoldenhuis/home_assistant_omnik_solar. For now, only manual install and install via custom repositories option in HACS

The Omnik solar sensor component will retrieve data from an Omnik solar inverter.
The values will be presented as sensors (or attributes of sensors) in [Home Assistant](https://home-assistant.io/).

> Note: Currently the Omnik Portal is not supported anymore. Omnik went bankrupt and the Omnik Portal API is not operational anymore.
You could consider moving to [OmnikPortal.net](https://omnikportal.net/), but I currently have no intention of supporting that portal.

> Note: Your Omnik inverter must support http calls which is used to retrieve data responses.
Some users indicated that their inverter not works and therefore no responses are received. For those the [omnik-inverter](https://github.com/robbinjanssen/home-assistant-omnik-inverter) custom integration might be a solution.


## HACS (Home Assistant Community Store)

This is a custom component. Custom components are not installed by default in your Home Assistant installation.
[HACS](https://custom-components.github.io/hacs/) is an Home Assistant store integration from which this integration can be easily installed and updated.
By using HACS you will also make sure that any new versions are installed by default and as simple as the installation itself.

## Manual installation

Create a directory called `omnik` in the `<config directory>/custom_components/` directory on your Home Assistant instance.
Install this component by copying the files in [`/custom_components/omnik/`]
(https://raw.githubusercontent.com/heinoldenhuis/home_assistant_omnik_solar/master/custom_components/omnik/__init__.py, 
https://raw.githubusercontent.com/heinoldenhuis/home_assistant_omnik_solar/master/custom_components/omnik/manifest.json and  https://raw.githubusercontent.com/heinoldenhuis/home_assistant_omnik_solar/master/custom_components/omnik/sensor.py) from this repo into the new `<config directory>/custom_components/omnik/` directory you just created

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
      dcinputvoltage:
      dcinputcurrent:
      acoutputvoltage:
      acoutputcurrent:
      acoutputfrequency:
      acoutputpower:
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
  * *hourstotal*: Sensor with the actual power value.
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

# Thanks
Big thanks to [@heinoldenhuis](https://github.com/heinoldenhuis) for the original integration.

