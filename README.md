# HA UPS MQTT Bridge

A simple Python bridge that polls UPS data from [Network UPS Tools (NUT)](https://networkupstools.org/) using `upsc` and publishes metrics to MQTT for integration with [Home Assistant](https://www.home-assistant.io/).

## Features

- Polls UPS metrics via `upsc`
- Publishes UPS status and sensor values to MQTT
- Auto-discovers in Home Assistant using MQTT Discovery
- Configurable via YAML
- Runs as a systemd service for reliability

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/zackwag/ha-ups-mqtt.git
cd ups-mqtt
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

Edit the `config.yaml` file and replace each occurence of `[CHANGEME]` with the correct information.

### 4. Test run

```bash
./venv/bin/python3 ha-ups-mqtt.py
```

## Run as a System Service (Optional, but recommended)

### 1. Copy the service file

```bash
sudo cp systemd/ha-ups-mqtt.service /etc/systemd/system/
```

### 2. Adjust paths if needed

Make sure the `ExecStart` and `WorkingDirectory` in `ha-ups-mqtt.service` point to your installation directory (default: `/opt/ha-ups-mqtt`).

### 3. Reload systemd and enable service

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ha-ups-mqtt
```

### 4. Check status

```bash
systemctl status ha-ups-mqtt
```

Logs can be viewed with:

```bash
journalctl -u ups-mqtt -f
```

## Home Assistant

With MQTT Discovery enabled, entities will appear automatically.

### Entities will be named

_(Assuming you have set the device name to `Den UPS`)_

- sensor.den_ups_battery_charge → **Den UPS Battery Charge**
- sensor.den_ups_output_voltage → **Den UPS Output Voltage**
- sensor.den_ups_status_data → **Den UPS Status Data**

### Example Sensors

- Battery Charge (%)
- Runtime Remaining (s → convert to h in HA)
- Input Voltage (V)
- Output Voltage (V)
- Load (%)
- Status (string)

## Contributing

Pull requests are welcome! If you have improvements (new sensors, config options, Dockerfile, etc.), open an issue or PR.
