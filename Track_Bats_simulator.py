#!/usr/bin/env python3

import asyncio
import sys
import numpy as np
from matplotlib import mlab
import time

from mavsdk import System
from mavsdk.offboard import (OffboardError, PositionNedYaw)
from rtlsdr import *

sdr = RtlSdr()

sdr.sample_rate = 2.4e6
sdr.center_freq = 150.5e6
sdr.gain = 5

num_samples = 512*2048

async def run():

    # Init the drone
    drone = System()
    await drone.connect(system_address="serial:///dev/serial0:921600")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Drone discovered with UUID: {state.uuid}")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok:
            print("Global position estimate ok")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Setting initial setpoint")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))

    print("-- Starting offboard")
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"Starting offboard mode failed with error code: {error._result.result}")
        print("-- Disarming")
        await drone.action.disarm()
        return

    print("-- Go 0m North, 0m East, 10m Up within local coordinate system")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -10.0, 0.0))
    async for position in drone.telemetry.position():
        altitude = position.relative_altitude_m
        if altitude > 9.5:
            break
    await asyncio.sleep(5)

    print("-- Go 0m North, 0m East, stay at 10m Up within local coordinate system, rotate 360 dgrees slowly")
    for i in range(0, 360, 3):
        await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -10.0, i))
        samples = sdr.read_samples(num_samples)
        Pxx, freqs = mlab.psd(samples, Fs=sdr.sample_rate)

        async for position in drone.telemetry.position():
            latitude = position.latitude_deg
            longitude = position.longitude_deg
            break

        latitude_a = np.full(len(freqs), latitude)
        longitude_a = np.full(len(freqs), longitude)
        freqs+=sdr.center_freq
        amplitude_dB = 10 * np.log10(np.abs(Pxx))
        i_a = np.full(len(freqs), i)

        original_stdout = sys.stdout 

        with open('filename.txt', 'a') as f:
            sys.stdout = f
            res = "\n".join("{} {} {} {} {}".format(x, y, z, w, i) for x, y, z, w, i in zip(freqs, amplitude_dB, latitude_a, longitude_a, i_a))
            print(res)
            sys.stdout = original_stdout

        if i == 360:
            break
    await asyncio.sleep(5)

    print("-- Stopping offboard")
    try:
        await drone.offboard.stop()
    except OffboardError as error:
        print(f"Stopping offboard mode failed with error code: {error._result.result}")

    print("Returning to launch")
    await drone.action.return_to_launch()





if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())
