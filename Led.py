from machine import Pin
import uasyncio

class LedState:
    on = 1
    off = 2
    flashing = 3

class Led:
    def __init__(self, pin: Pin, initialState = LedState.off) -> None:
        self.pin = pin
        self.period = 1000
        self.state = initialState

    def on(self):
        self.state = LedState.on

    def off(self):
        self.state = LedState.off

    def flash(self, periodMs = 1000):
        self.period = periodMs
        self.state = LedState.flashing

    async def loop(self):
        while True:
            if self.state == LedState.flashing:
                self.pin.on()
                await uasyncio.sleep_ms(int(self.period/2))
                self.pin.off()
                await uasyncio.sleep_ms(int(self.period/2))
            elif self.state == LedState.on:
                self.pin.on()
                await uasyncio.sleep_ms(500)
            else:
                self.pin.off()
                await uasyncio.sleep_ms(500)
