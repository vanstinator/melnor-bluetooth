# Melnor Bluetooth

![PyPI](https://img.shields.io/pypi/v/melnor-bluetooth?style=flat-square) ![Codecov branch](https://img.shields.io/codecov/c/github/vanstinator/melnor-bluetooth/main?style=flat-square) ![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/vanstinator/melnor-bluetooth/Build%20and%20Release/main?style=flat-square)
![PyPI - Downloads](https://img.shields.io/pypi/dm/melnor-bluetooth?style=flat-square)

Melnor Bluetooth is a reverse engineered implementation of the Bluetooth protocol for all "smart" bluetooth-enabled watering valves under the Melnor, EcoAquastar, Eden, and other brands.

The library _should_ run on MacOS, Linux, or Windows. It's primarily developed on MacOS and other platforms likely have bugs. PRs and tests are welcome to improve quality across all platforms.


### Getting Started

#### CLI
A simple CLI has been provided for basic debugging purposes. It's not intended for any real use and isn't suitable for running a valve in the real world.

This project uses poetry for dependency management and building. Running this project locally is as simple as the following steps:

1. Clone the repository
1. `poetry install`
1. `poetry run cli.py`


The python API has been designed to be as easy to use as possible. A few examples are provided below:

#### Read battery state
```python
import asyncio

from bleak import BleakScanner  # type: ignore - bleak has bad export types

from melnor_bluetooth.device import Device

ADDRESS = "00:00:00:00:00"  # fill with your device mac address


async def main():

    ble_device = await BleakScanner.find_device_by_address(ADDRESS)
    if ble_device is not None:
        device = Device(ble_device)
        await device.connect()
        await device.fetch_state()

        print(device.battery_level)

        await device.disconnect()


asyncio.run(main())

```

#### Turn on a zone
```python
import asyncio

from bleak import BleakScanner  # type: ignore - bleak has bad export types

from melnor_bluetooth.device import Device

address = "00:00:00:00:00"  # fill with your device mac address


async def main():
    ble_device = await BleakScanner.find_device_by_address(ADDRESS)
    if ble_device is not None:
        device = Device(ble_device)
        await device.connect()
        await device.fetch_state()

        device.zone1.is_watering = True

        await device.push_state()
        await device.disconnect()


asyncio.run(main())
```
