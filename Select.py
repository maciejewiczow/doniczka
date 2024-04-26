from lib.ha_mqtt_device import BaseEntity, Device
from lib.lib.mqtt_as import MQTTClient


class Select(BaseEntity):
    def __init__(
        self,
        mqtt: MQTTClient,
        name: bytes,
        options,
        device: Device,
        initial_value: bytes,
        unique_id=None,
        object_id=None,
        node_id=None,
        discovery_prefix=b'homeassistant',
        extra_conf=None,
        entity_category=None,
        icon=None,
        on_change=None
    ):
        command_t_suffix = b'set'
        self.on_change = on_change

        config = {
            'command_topic': b'~/'+command_t_suffix,
            'options': options,
        }

        if extra_conf:
            config.update(extra_conf)

        self.value = initial_value

        super().__init__(mqtt,
            name,
            b'select',
            device,
            unique_id,
            object_id,
            node_id,
            discovery_prefix,
            config,
            entity_category,
            icon
        )
        self.command_topic = self.base_topic + b'/' + command_t_suffix

    async def init_mqtt(self):
        await super().init_mqtt()
        await self.mqtt.subscribe(self.command_topic)
        await self.publish_state()

    async def publish_state(self):
        await super().publish_state(self.value)

    async def handle_mqtt_message(self, topic: bytes, message):
        if topic == self.command_topic:
            self.value = message
            await self.publish_state()

            if self.on_change:
                await self.on_change(self.value)
