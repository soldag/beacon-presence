import functools
from ruamel.yaml import YAML


class Configuration:
    def __init__(self):
        self.data = None

    @property
    def mqtt_host(self):
        return self.get_config('mqtt', 'host', default='localhost')

    @property
    def mqtt_port(self):
        return self.get_config('mqtt', 'port', data_type=int, default=1883)

    @property
    def mqtt_username(self):
        return self.get_config('mqtt', 'username')

    @property
    def mqtt_password(self):
        return self.get_config('mqtt', 'password')

    @property
    def mqtt_tls(self):
        return self.get_config('mqtt', 'tls', data_type=bool, default=False)

    @property
    def mqtt_client_id(self):
        return self.get_config('mqtt', 'client_id', default='beacon-presence')

    @property
    def mqtt_root_topic(self):
        return self.get_config('mqtt', 'root_topic', default='beacon-presence')

    @property
    def mqtt_keep_alive(self):
        return self.get_config('mqtt', 'keep_alive', data_type=int, default=10)

    @property
    def hci_device(self):
        return self.get_config('hci', 'device', default='hci0')

    @property
    def beacon_expiration(self):
        return self.get_config('behavior', 'beacon_expiration', data_type=int, default=300)

    @property
    def beacons(self):
        beacons = []
        for beacon in self.get_config('beacons', default=[]):
            if not beacon.get('id') or not beacon.get('uuid'):
                continue
            beacons.append({
                'id': beacon['id'],
                'uuid': beacon['uuid'].upper(),
            })

        return beacons

    def load(self, path):
        with open(path, mode='r') as f:
            self.data = YAML().load(f)

    def get_config(self, *keys, data_type=None, default=None):
        if self.data is None:
            return default

        try:
            value = functools.reduce(lambda acc, key: acc[key], keys, self.data)
            return data_type(value) if data_type else value
        except (KeyError, TypeError):
            return default
