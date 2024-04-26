from AveragingThrottledSensor import AveragingThrottledSensor
from Button import Button
from FileSyncedDict import FileSyncedDict
from Number import Number
from Select import Select
from Switch import Switch
from lib.ha_mqtt_device import BinarySensor, Device
from lib.lib.mqtt_as import MQTTClient
from lib.wifiConfig.tryConnectingToKnownNetworks import tryConnectingToKnownNetworks
import uasyncio
from secrets import mqtt_password, mqtt_user
from machine import Pin, ADC
import gc

gc.collect()

data = FileSyncedDict(
    'data.json',
    {
        'airMoistureReading': None,
        'waterMoistureReading': None,
        'targetMoisture': None,
        'mode': 'Manual'
    }
)

waterPumpPin = Pin(22, Pin.OUT)
lowWaterLevelSensorPin = Pin(21, Pin.IN, Pin.PULL_UP)
moistureSensorPin = ADC(Pin(28))

def map_range(x, src, dest):
    src_min, src_max = src
    dest_min, dest_max = dest

    return ((x-src_min)/(src_max-src_min))*(dest_max-dest_min)+dest_min

client = MQTTClient(
    port=1883,
    user=mqtt_user,
    password=mqtt_password,
    server='192.168.88.19',
    queue_len=10,
    ssid='',
    wifi_pw=''
)

device = Device(
    mqtt=client,
    manufacturer=b'DIY',
    model=b'Raspberry Pi PICO',
    name=b'Autowatering flower pot',
    device_id=b'autowatering-flower-pot'
)

def triggerWaterPump(value: bool):
    if isWaterLevelLow or modeSelect.value == 'Automatic':
        return False

    if value:
        waterPumpPin.on()
    else:
        waterPumpPin.off()

    return True

wateringSwitch = Switch(
    mqtt=client,
    name=b'Water pump',
    device=device,
    device_class=b'switch',
    object_id=b'flower-pot-water-pump',
    icon=b"mdi:water-pump",
    on_change=triggerWaterPump
)

lowWaterLevelSensor = BinarySensor(
    mqtt=client,
    name=b'Tank water level',
    device=device,
    device_class=b'problem',
    entity_category=b'diagnostic',
    object_id=b'flower-pot-low-water-sensor',
    icon=b'mdi:water-alert'
)

async def updateSavedMode(value: bytes):
    data['mode'] = value.decode()

    if value == b'Manual':
        wateringSwitch.is_on = False
        await wateringSwitch.publish_state()
        waterPumpPin.off()

modeSelect = Select(
    mqtt=client,
    name=b'Operation mode',
    initial_value=data['mode'],
    device=device,
    object_id=b'flower-pot-operation-mode-select',
    options=[
        b'Automatic',
        b'Manual'
    ],
    on_change=updateSavedMode
)

def updateSavedTargetLevel(value: float):
    data['targetMoisture'] = value

targetMoistureLevelHANumber = Number(
    mqtt=client,
    device=device,
    name=b'Target moisture level',
    icon=b'mdi:water-outline',
    initialValue=data['targetMoisture'],
    maxValue=100,
    minValue=0,
    step=1,
    mode=b'slider',
    object_id=b'flower-pot-target-moisture-level',
    on_change=updateSavedTargetLevel,
    unit_of_measurement=b'%',
)

moistureSensor = AveragingThrottledSensor(
    mqtt=client,
    window_size=30,
    device=device,
    name=b'Moisture',
    object_id=b'flower-pot-moisture',
    icon=b'mdi:water',
    state_class='measurement',
    throttle_ms=5_000,
    extra_conf={
        'unit_of_measurement': b'%'
    }
)

async def setAirMoistureReference():
    data['airMoistureReading'] = moistureSensorPin.read_u16()

setAirMoistureReferenceButton = Button(
    mqtt=client,
    device=device,
    on_press=setAirMoistureReference,
    entity_category='config',
    object_id=b'flower-pot-moisture-air-set',
    icon=b'mdi:water-sync',
    name=b'Set air moisture ref value'
)

async def setWaterMoistureReference():
    data['waterMoistureReading'] = moistureSensorPin.read_u16()

moistureReading = None

setWaterMoistureReferenceButton = Button(
    mqtt=client,
    device=device,
    on_press=setWaterMoistureReference,
    entity_category='config',
    icon=b'mdi:water-sync',
    object_id=b'flower-pot-moisture-water-set',
    name=b'Set water moisture ref value'
)

async def init_mqtt_devices():
    await wateringSwitch.init_mqtt()
    await lowWaterLevelSensor.init_mqtt()
    await modeSelect.init_mqtt()
    await moistureSensor.init_mqtt()
    await setAirMoistureReferenceButton.init_mqtt()
    await setWaterMoistureReferenceButton.init_mqtt()
    await targetMoistureLevelHANumber.init_mqtt()
    await device.init_mqtt()

async def mqtt_up_watcher():
    while True:
        await client.up.wait() # type:ignore

        await init_mqtt_devices()

        client.up.clear()

async def mqtt_messages_handler():
    async for topic, msg, retained in client.queue: # type: ignore
        print('Message received', topic, msg)
        await device.handle_mqtt_message(topic, msg)
        await wateringSwitch.handle_mqtt_message(topic, msg)
        await modeSelect.handle_mqtt_message(topic, msg)
        await setAirMoistureReferenceButton.handle_mqtt_message(topic, msg)
        await setWaterMoistureReferenceButton.handle_mqtt_message(topic, msg)
        await targetMoistureLevelHANumber.handle_mqtt_message(topic, msg)

async def main():
    ip, ssid, _ = await tryConnectingToKnownNetworks(apName="Smart plant pot", domain="config.smart-pot")
    gc.collect()

    print(f'Connected to "{ssid}" with ip {ip}')

    await client.connect() # type:ignore
    print('Connected to mqtt')

    await init_mqtt_devices()

    print('Mqtt devices initialized')

    await uasyncio.gather(mqtt_up_watcher(), mqtt_messages_handler(), hardwareMain()) # type:ignore

lastIsWaterLevelLow = None
isWaterLevelLow = True

async def waterLevelWatcher():
    global lastIsWaterLevelLow
    global isWaterLevelLow
    while True:
        isWaterLevelLow = lowWaterLevelSensorPin.value() == 1

        if lastIsWaterLevelLow != isWaterLevelLow:
            await lowWaterLevelSensor.publish_state(isWaterLevelLow)
            waterPumpPin.off()
            wateringSwitch.is_on = False
            await wateringSwitch.publish_state()

        lastIsWaterLevelLow = isWaterLevelLow
        await uasyncio.sleep_ms(700)

moistureLowerThreshold = 5
moistureOvershoot = 5

oldHysteresisResult = False
def hysteresis(value: float):
    global oldHysteresisResult

    result = False

    maxVal = targetMoistureLevelHANumber.value + moistureOvershoot
    minVal = targetMoistureLevelHANumber.value - moistureLowerThreshold

    if value > maxVal:
        result = False
    elif value < minVal:
        result = True
    else:
        result = oldHysteresisResult

    oldHysteresisResult = result
    return result

lastOn = False
async def autoModeLoop():
    global isWaterLevelLow
    global moistureLowerThreshold
    global moistureOvershoot
    global lastOn

    while True:
        await uasyncio.sleep_ms(200)

        if isWaterLevelLow:
            continue

        if modeSelect.value != 'Automatic':
            lastOn = False
            continue

        if moistureReading is None:
            continue

        hysteresisValue = hysteresis(moistureReading)

        if hysteresisValue and not lastOn:
            waterPumpPin.on()
            wateringSwitch.is_on = True
            await wateringSwitch.publish_state()
            lastOn = True
        elif not hysteresisValue and lastOn:
            waterPumpPin.off()
            wateringSwitch.is_on = False
            await wateringSwitch.publish_state()
            lastOn = False

async def moistureReadingWatcher():
    global moistureReading

    while True:
        if data['airMoistureReading'] is not None and data['waterMoistureReading'] is not None:
            moistureReading = map_range(moistureSensorPin.read_u16(), (data['airMoistureReading'], data['waterMoistureReading']), (0, 100))
            await moistureSensor.publish_state(moistureReading)

        await uasyncio.sleep_ms(1000)

async def hardwareMain():
    await uasyncio.gather(moistureReadingWatcher(), waterLevelWatcher(), autoModeLoop()) # type:ignore

uasyncio.run(main())
