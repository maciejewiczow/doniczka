from lib.ha_mqtt_device import BaseEntity, Device
from lib.lib.mqtt_as import MQTTClient


class Button(BaseEntity):
    payload_press = b'1'

    def __init__(
        self,
        mqtt: MQTTClient,
        name: bytes,
        device: Device,
        object_id = None,
        icon = None,
        # 'config', 'diagnostic' or None
        entity_category = None,
        unique_id = None,
        node_id=None,
        discovery_prefix=b'homeassistant',
        extra_conf=None,
        on_press = None
    ):
        config = {}

        self.on_press = on_press

        cmd_t_suffix = b'press'

        config = {
            'cmd_t': b'~/' + cmd_t_suffix,
            'payload_press': self.payload_press
        }

        if extra_conf:
            config.update(extra_conf)

        super().__init__(
            unique_id=unique_id,
            device=device,
            extra_conf=config,
            mqtt=mqtt,
            name=name,
            component=b'button',
            object_id=object_id,
            node_id=node_id,
            discovery_prefix=discovery_prefix,
            entity_category=entity_category,
            icon=icon,
        )

        self.command_topic = self.base_topic + '/' + cmd_t_suffix

    async def init_mqtt(self):
        await super().init_mqtt()
        await self.mqtt.subscribe(self.command_topic)

    async def handle_mqtt_message(self, topic: bytes, message):
        await super().handle_mqtt_message(topic, message)

        if topic == self.command_topic and message == self.payload_press and self.on_press:
            await self.on_press()
