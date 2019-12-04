import board, neopixel
import os, asyncio, threading, random
from dotenv import load_dotenv
from azure.iot.device.aio import IoTHubDeviceClient, ProvisioningDeviceClient
from azure.iot.device import MethodResponse

load_dotenv()

pixel_count = 20
pixels = neopixel.NeoPixel(board.D18, pixel_count)

mode = 'off'

id_scope = os.getenv('ID_SCOPE')
device_id = os.getenv('DEVICE_ID')
primary_key = os.getenv('PRIMARY_KEY')

async def main():
    # provision the device
    async def register_device():
        provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
            provisioning_host='global.azure-devices-provisioning.net',
            registration_id=device_id,
            id_scope=id_scope,
            symmetric_key=primary_key,
        )

        return await provisioning_device_client.register()

    results = await asyncio.gather(register_device())
    registration_result = results[0]

    # build the connection string
    conn_str='HostName=' + registration_result.registration_state.assigned_hub + \
                ';DeviceId=' + device_id + \
                ';SharedAccessKey=' + primary_key

    # The client object is used to interact with your Azure IoT Central.
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)

    # connect the client.
    print('Connecting')
    await device_client.connect()
    print('Connected')

    # listen for commands
    async def command_listener(device_client):
        global mode
        while True:
            method_request = await device_client.receive_method_request()
            mode = method_request.name
            print('Mode set:', mode)
            payload = {'result': True, 'data': mode}
            method_response = MethodResponse.create_from_method_request(
                method_request, 200, payload
            )
            await device_client.send_method_response(method_response)

    # async loop that controls the lights
    async def main_loop():
        global mode
        while True:
            if mode == 'flashing_colours':
                for x in range (0, pixel_count):
                    pixels[x] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            else:
                pixels.fill((0, 0, 0))
            await asyncio.sleep(1)

            print('polling - mode is', mode)

    listeners = asyncio.gather(command_listener(device_client))

    await main_loop()

    # Cancel listening
    listeners.cancel()

    # Finally, disconnect
    await device_client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())