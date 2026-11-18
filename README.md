# Infrared learning remote

[![Open your Home Assistant instance and open a repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=balloobbot&repository=infrared-learning-remote&category=integration)

A Home Assistant helper that learns commands from a remote and sends them again as buttons.

## Requirements

- Home Assistant 2026.11.0 or later
- An infrared emitter entity, to send the commands
- An infrared receiver entity, to learn the commands from your remote

ESPHome, Broadlink, MQTT and ZHA devices can provide these entities.

## Installation

### HACS

1. In HACS, add this repository as a custom repository of the type **Integration**.
2. Download **Infrared learning remote**.
3. Restart Home Assistant.

### Manual

1. Copy `custom_components/infrared_learning_remote` into the `custom_components` folder of your Home Assistant configuration.
2. Restart Home Assistant.

## Use

### Create a device

1. Go to **Settings** > **Devices & services** > **Helpers**.
2. Select **Create helper** > **Infrared learning remote**.
3. Enter the name of the device that you control, for example, Living room TV.
4. Select the infrared emitter that sends the commands.

### Learn a command

1. Open the helper and select **Add command**.
2. Select the infrared receiver.
3. Select **Submit**. Within 30 seconds, point your remote at the receiver and press the button.
4. Enter a name for the command, for example, Power.

Each command is a button on the device. Press the button to send the command through the emitter.

If no signal arrives within 30 seconds, the form shows again. Select **Submit** to try again.

## How it works

The receiver records the signal as a list of pulse and pause durations. The helper stores this list in the command and sends it again without changes.

Most receivers do not report the carrier frequency. In that case, the helper uses 38 kHz. Most consumer remotes use this frequency.

## Development

```bash
uv venv --python 3.14
```

```bash
uv pip install -r requirements_test.txt
```

```bash
uv run pytest
```
