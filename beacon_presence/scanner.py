import re
import asyncio
import logging
from dataclasses import dataclass


@dataclass
class BeaconAdvertisement:
    uuid: str
    major: int
    minor: int
    power: int
    rssi: int


class BeaconScanner:
    ADVERTISEMENT_PATTERNS = (
        re.compile(r'(043E270201)([0-9A-F]{26})(0215)(?P<uuid>[0-9A-F]{32})(?P<major>[0-9A-F]{4})(?P<minor>[0-9A-F]{4})(?P<power>[0-9A-F]{2})(?P<rssi>[0-9A-F]{2})'),
        re.compile(r'(043E2A0201)([0-9A-F]{18})(0201)([0-9A-F]{10})(0215)(?P<uuid>[0-9A-F]{32})(?P<major>[0-9A-F]{4})(?P<minor>[0-9A-F]{4})(?P<power>[0-9A-F]{2})(?P<rssi>[0-9A-F]{2})'),
        re.compile(r'(043E2[AB]0201)([0-9A-F]{26})(0201)([0-9A-F]{14})(0215)(?P<uuid>[0-9A-F]{32})(?P<major>[0-9A-F]{4})(?P<minor>[0-9A-F]{4})(?P<power>[0-9A-F]{2})(?P<rssi>[0-9A-F]{2})'),
    )

    def __init__(self, config, beacon_manager):
        self.config = config
        self.beacon_manager = beacon_manager
        self.scan_proccess = None
        self.dump_process = None

    async def run(self):
        try:
            await self.reset_hci_device()
            await self.start_scan()
            await asyncio.gather(
                self.monitor_scan(),
                self.process_packets(),
            )
        finally:
            await self.stop_scan()

    async def reset_hci_device(self):
        process = await asyncio.create_subprocess_exec(
            'hciconfig', self.config.hci_device, 'reset',
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        await self.monitor_process('hci reset', process)

    async def start_scan(self):
        logging.debug('Start scan processes...')
        self.scan_process, self.dump_process = await asyncio.gather(
            asyncio.create_subprocess_exec(
                'hcitool', 'lescan', '--duplicates',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            ),
            asyncio.create_subprocess_exec(
                'hcidump', '-i', self.config.hci_device, '--raw',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
        )
        logging.debug('Started scan processes...')

    async def monitor_scan(self):
        await asyncio.gather(
            self.monitor_process('hci scan', self.scan_process),
            self.monitor_process('hci dump', self.dump_process),
        )

    async def monitor_process(self, name, process):
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            logging.error(line.decode().rstrip())
        await process.wait()
        if process.returncode != 0:
            raise OSError(f'The {name} process exited with code {process.returncode}')

    async def process_packets(self):
        packet = ''
        while True:
            line = await self.dump_process.stdout.readline()
            if not line:
                break
            data = line.decode('ascii').rstrip().replace(' ', '')

            # Packets start with ">"
            if data.startswith('>'):
                # Process completed packet
                advertisement = self.parse_packet(packet)
                if advertisement:
                    logging.debug(f'Received advertisement from beacon {advertisement.uuid}')
                    await self.beacon_manager.process_advertisement(advertisement)

                # Start new packet
                packet = data[1:]
            elif packet:
                # Continue building packet
                packet += data

    def parse_packet(self, packet):
        match = next((r.match(packet) for r in self.ADVERTISEMENT_PATTERNS), None)
        if match:
            return BeaconAdvertisement(
                uuid=self.format_uuid(match.group('uuid')),
                major=int(match.group('major'), 16),
                minor=int(match.group('minor'), 16),
                power=int(match.group('power'), 16) - 256,
                rssi=int(match.group('rssi'), 16) - 256,
            )

    @staticmethod
    def format_uuid(uuid):
        return f'{uuid[:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:]}'

    async def stop_scan(self):
        logging.debug('Stopping scan processes...')
        processes = [p for p in (self.scan_process, self.dump_process)
                     if p is not None and p.returncode is None]
        for process in processes:
            process.terminate()
        await asyncio.gather(
            *(process.wait() for process in processes)
        )
        logging.debug('Stopped scan processes...')
