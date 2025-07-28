#!/usr/bin/env python3
"""
Test script - basic connection and status check
Usage: poetry run python test.py
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta

import aiohttp
from dotenv import load_dotenv

from python_snoo.baby import Baby
from python_snoo.snoo import Snoo

load_dotenv()
EMAIL = os.getenv("SNOO_EMAIL")
PASSWORD = os.getenv("SNOO_PASSWORD")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Test python-snoo library functionality")
    parser.add_argument("--log-diaper", action="store_true", help="Log a test mixed diaper change (pee and poo)")
    parser.add_argument(
        "--diaper-note", type=str, default="Test diaper change", help="Note to add to diaper change log"
    )
    return parser.parse_args()


async def authenticate_and_get_devices(snoo):
    print("🔐 Authenticating...")
    await snoo.authorize()
    print("✅ Authentication successful!")

    print("📱 Getting devices...")
    devices = await snoo.get_devices()
    print(f"✅ Found {len(devices)} device(s)")
    return devices


async def test_device_status(snoo, device):
    print(f"🎯 Testing device: {device.name}")

    print("📊 Getting status...")

    # Dummy callback for our test connection
    def connection_callback(data):
        pass

    snoo.start_subscribe(device, connection_callback)
    status = await snoo.get_status(device)
    print(f"✅ Current status: {status}")


async def get_baby_info(baby):
    baby_data = await baby.get_status()
    print(f"  ✅ Baby: {baby_data.babyName}")
    print(f"     Birth Date: {baby_data.birthDate}")
    print(f"     Sex: {baby_data.sex}")
    print(f"     Weaning: {baby_data.settings.weaning}")
    print(f"     Responsiveness Level: {baby_data.settings.responsivenessLevel}")
    print(f"     Soothing Level Volume: {baby_data.settings.soothingLevelVolume}")


def parse_activities(activities):
    feeding_activities = []
    diaper_activities = []

    for activity in activities:
        activity_type = activity.get("type", "").lower()
        if "breastfeeding" in activity_type:
            feeding_activities.append(activity)
        elif "diaper" in activity_type:
            diaper_activities.append(activity)

    return feeding_activities, diaper_activities


def display_activities(feeding_activities, diaper_activities):
    print(f"     Feeding activities: {len(feeding_activities)}")
    for i, feeding in enumerate(feeding_activities[:3]):
        start_time = feeding.get("startTime", "N/A")
        end_time = feeding.get("endTime", "N/A")
        duration = feeding.get("data", {}).get("totalDuration", "N/A")
        print(f"       Feeding {i + 1}: {start_time} - {end_time} ({duration}s)")

    print(f"     Diaper activities: {len(diaper_activities)}")
    for i, diaper in enumerate(diaper_activities[:3]):
        time = diaper.get("startTime", "N/A")
        types = diaper.get("data", {}).get("types", [])
        print(f"       Diaper {i + 1}: {time} - {types}")


async def test_activity_data(baby, args):
    print("  📊 Getting activity data...")
    activity_data = await baby.get_activity_data(from_date=datetime.now() - timedelta(days=1), to_date=datetime.now())
    print("  ✅ Activity data retrieved!")

    for activity in activity_data:
        print(activity)


async def test_diaper_logging(baby, note):
    print("  🧷 Testing diaper change logging...")
    result = await baby.log_diaper_change(["pee", "poo"], note=note)
    print(f"  ✅ Mixed diaper logged: {result}")


async def test(test_args):
    async with aiohttp.ClientSession() as session:
        snoo = Snoo(EMAIL, PASSWORD, session)

        devices = await authenticate_and_get_devices(snoo)

        if devices:
            device = devices[0]
            await test_device_status(snoo, device)

            if device.babyIds:
                print(f"👶 Found {len(device.babyIds)} baby(ies) associated with device")
                for baby_id in device.babyIds:
                    print(f"  📋 Getting data for baby ID: {baby_id}")
                    baby = Baby(baby_id, snoo)
                    await get_baby_info(baby)
                    await test_activity_data(baby, test_args)

            else:
                print("👶 No babies associated with this device")

        await snoo.disconnect()
        print("✅ Test completed successfully!")


if __name__ == "__main__":
    args = parse_arguments()

    if not EMAIL or not PASSWORD:
        print("❌ Error: SNOO_EMAIL and SNOO_PASSWORD must be set")
        print("📝 Copy .env.example to .env and update with your credentials, or set environment variables explicitly.")
        sys.exit(1)

    asyncio.run(test(args))
