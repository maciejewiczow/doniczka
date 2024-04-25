from lib.ha_mqtt_device import BaseEntity, Device
from lib.lib.mqtt_as import MQTTClient


class Number(BaseEntity):
    def __init__(self,
         mqtt: MQTTClient,
         name: bytes,
         device: Device,
         initialValue: float,
         minValue=None,
         maxValue=None,
         step=None,
         #  'box', 'slider' or None
         mode=None,
         unit_of_measurement=None,
         unique_id=None,
         object_id=None,
         node_id=None,
         discovery_prefix=b'homeassistant',
         extra_conf=None,
         entity_category=None,
         icon=None,
         on_change=None
    ):
        self.value = initialValue
        self.on_change = on_change

        config = {}

        cmd_t_suffix = b'set'

        config = {
            'cmd_t': b'~/' + cmd_t_suffix,
        }

        if minValue:
            config['min'] = minValue

        if maxValue:
            config['max'] = maxValue

        if step:
            config['step'] = step

        if mode:
            config['mode'] = mode

        if unit_of_measurement:
            config['unit_of_measurement'] = unit_of_measurement

        if extra_conf:
            config.update(extra_conf)

        super().__init__(
            mqtt,
            name,
            b'number',
            device,
            unique_id,
            object_id,
            node_id,
            discovery_prefix,
            config,
            entity_category,
            icon
        )

        self.command_topic = self.base_topic + '/' + cmd_t_suffix

    async def init_mqtt(self):
        await super().init_mqtt()
        await self.mqtt.subscribe(self.command_topic)
        await self.publish_state()

    async def publish_state(self):
        await super().publish_state(str(self.value))

    async def handle_mqtt_message(self, topic: bytes, message):
        if topic == self.command_topic:
            self.value = float(message)
            await self.publish_state()

            if self.on_change:
                self.on_change(self.value)
