from lib.ha_mqtt_device import BaseEntity, Device
from lib.lib.mqtt_as import MQTTClient

class Switch(BaseEntity):
    payload_on = b'1'
    payload_off = b'0'

    def __init__(
        self,
        mqtt: MQTTClient,
        name: bytes,
        device: Device,
        object_id = None,
        icon = None,
        # 'config', 'diagnostic' or None
        entity_category = None,
        # 'switch', 'outlet' or None
        device_class = None,
        unique_id = None,
        node_id=None,
        discovery_prefix=b'homeassistant',
        extra_conf=None,
        on_change=None
    ):
        self.on_change = on_change
        config = {}

        if device_class:
            config['device_class'] = device_class

        cmd_t_suffix = b'set'

        config = {
            'cmd_t': b'~/' + cmd_t_suffix,
            'payload_on': self.payload_on,
            'payload_off': self.payload_off
        }

        if extra_conf:
            config.update(extra_conf)

        self.is_on = False

        super().__init__(
            unique_id=unique_id,
            device=device,
            extra_conf=config,
            mqtt=mqtt,
            name=name,
            component=b'switch',
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
        await self.publish_state()

    async def publish_state(self, is_on = None):
        if is_on == None:
            is_on = self.is_on
        else:
            self.is_on = is_on

        await super().publish_state(self.payload_on if is_on else self.payload_off)

    # TODO: handle HA start

    async def handle_mqtt_message(self, topic: bytes, message):
        if topic == self.command_topic:
            await self._handle_command(message)

    async def _handle_command(self, raw_message):
        newIsOn = raw_message == self.payload_on

        if self.is_on != newIsOn:
            doPublish = True
            if self.on_change:
                doPublish = self.on_change(newIsOn)

            if doPublish:
                await super().publish_state(self.payload_on if newIsOn else self.payload_off)

        self.is_on = newIsOn
