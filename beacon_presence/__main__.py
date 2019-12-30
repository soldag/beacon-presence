import signal
import asyncio
import logging
import argparse

from beacon_presence.config import Configuration
from beacon_presence.mqtt import MqttClient
from beacon_presence.manager import BeaconManager
from beacon_presence.scanner import BeaconScanner


def setup_logging(verbose):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    # Suppress unecessary logging from dependencies
    logging.getLogger('transitions.core').setLevel(logging.CRITICAL)


async def async_main():
    parser = argparse.ArgumentParser(description='Presence detection using BLE beacons')
    parser.add_argument('--config', '-c', help='Path of the configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show debug logs')
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)
    logging.info('Starting beacon-presence...')

    config = Configuration()
    if args.config:
        config.load(args.config)
    mqtt_client = MqttClient(config)
    beacon_manager = BeaconManager(config, mqtt_client)
    beacon_scanner = BeaconScanner(config, beacon_manager)

    try:
        await mqtt_client.connect()
        await asyncio.gather(
            beacon_manager.run(),
            beacon_scanner.run(),
        )
    finally:
        await mqtt_client.disconnect()


def main():
    loop = asyncio.get_event_loop()
    task = loop.create_task(async_main())

    # Allow graceful exit from system signal
    for s in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(s, lambda: shutdown(task))

    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass

    loop.close()


def shutdown(task):
    logging.info('Stopping beacon-presence gracefully...')
    task.cancel()


if __name__ == '__main__':
    main()
