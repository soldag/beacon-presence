import logging

from hbmqtt.client import MQTTClient


class MqttClient:
    def __init__(self, config):
        self.config = config
        self.client = MQTTClient(
            client_id=config.mqtt_client_id,
            config={
                'keep_alive': config.mqtt_keep_alive,
            },
        )

    async def connect(self):
        uri = 'mqtts://' if self.config.mqtt_tls else 'mqtt://'
        if self.config.mqtt_username:
            uri += self.config.mqtt_username
            if self.config.mqtt_password:
                uri += f':{self.config.mqtt_password}'
            uri += '@'
        uri += f'{self.config.mqtt_host}:{self.config.mqtt_port}'

        await self.client.connect(uri)

    async def disconnect(self):
        await self.client.disconnect()

    async def publish_state(self, beacon, state):
        topic = f'{self.config.mqtt_root_topic}/{beacon["id"]}/state'
        logging.debug(f'Publish to {topic}: {state}')
        await self.client.publish(topic, state.encode(), retain=True)
