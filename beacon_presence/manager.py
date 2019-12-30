import time
import asyncio
import logging


class BeaconManager:
    def __init__(self, config, mqtt_client):
        self.config = config
        self.mqtt_client = mqtt_client

        self.last_seen = {}
        self.present_beacons = set()
        self.known_beacons = {beacon['uuid']: beacon for beacon in config.beacons}

    async def run(self):
        # Initialize known beacons as not_home if no advertisement
        # has been received after expiration time
        await asyncio.sleep(self.config.beacon_expiration)
        await asyncio.gather(
            *(self.set_beacon_away(beacon)
              for uuid, beacon in self.known_beacons.items()
              if uuid not in self.present_beacons)
        )

        # Check constantly for expired beacons
        await self.watch_present_beacons()

    async def watch_present_beacons(self):
        while True:
            now = time.time()
            for uuid in list(self.present_beacons):
                if now - self.last_seen[uuid] >= self.config.beacon_expiration:
                    await self.set_beacon_away(self.known_beacons[uuid])

            await asyncio.sleep(1)

    async def process_advertisement(self, advertisement):
        # Ignore unknown beacons
        beacon = self.known_beacons.get(advertisement.uuid)
        if beacon is None:
            logging.debug(f'Beacon {advertisement.uuid} is unknown and thus ignored')
            return

        if beacon['uuid'] not in self.present_beacons:
            await self.set_beacon_home(beacon)

        self.last_seen[beacon['uuid']] = time.time()

    async def set_beacon_home(self, beacon):
        logging.info(f'[ARRIVAL] {beacon["id"]} ({beacon["uuid"]})')
        self.present_beacons.add(beacon['uuid'])
        await self.mqtt_client.publish_state(beacon, 'home')

    async def set_beacon_away(self, beacon):
        logging.info(f'[DEPARTURE] {beacon["id"]} ({beacon["uuid"]})')
        self.present_beacons.discard(beacon['uuid'])
        await self.mqtt_client.publish_state(beacon, 'not_home')
