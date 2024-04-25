[CmdletBinding()]
param (
    [Parameter()]
    [String]
    $PortName = "COM6"
)

mpremote connect $PortName mip install "github:maciejewiczow/rpi-wifi-config"
mpremote connect $PortName mip install "github:maciejewiczow/micropython-ha-mqtt-device"
