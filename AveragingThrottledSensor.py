import time
from lib.ha_mqtt_device import Device, Sensor
from lib.lib.mqtt_as import MQTTClient
import math

class AveragingThrottledSensor(Sensor):
    def __init__(
        self,
        mqtt: MQTTClient,
        name: bytes,
        object_id: bytes,
        device: Device,
        window_size: int,
        throttle_ms: int,
        node_id=None,
        discovery_prefix=b'homeassistant',
        state_class=None,
        extra_conf=None,
        icon=None,
        entity_category=None
    ):
        super().__init__(
            mqtt,
            name,
            object_id,
            device,
            node_id,
            discovery_prefix,
            state_class,
            extra_conf,
            icon,
            entity_category
        )
        self.values = []
        self.window_size = window_size
        self.current_entry = 0
        self.throttle_period_ms = throttle_ms
        self.time_of_last_publish = 0

    async def _actually_publish(self):
        now = time.ticks_ms()
        time_since_last_call = time.ticks_diff(now, self.time_of_last_publish)

        if time_since_last_call > self.throttle_period_ms:
            self.time_of_last_publish = now
            return await super().publish_state(str(math.floor(sum(self.values)/self.window_size)))

    async def publish_state(self, state):
        if len(self.values) == self.window_size:
            self.values[self.current_entry] = state
        else:
            self.values.append(state)

        if len(self.values) == self.window_size:
            await self._actually_publish()

        self.current_entry = (self.current_entry + 1) % self.window_size
