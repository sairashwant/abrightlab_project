"""Driving times from OpenStreetMap, using the free public OSRM server."""
import math
import time

import requests

online = True


def estimate(points):
    """Straight-line miles x 1.3, at 28 mph."""
    miles = lambda a, b: math.hypot((b["lat"] - a["lat"]) * 69,
                                    (b["lon"] - a["lon"]) * 69 * math.cos(math.radians(a["lat"])))
    return [[miles(a, b) * 1.3 / 28 for b in points] for a in points]


def drive_hours(points):
    """Driving hours between every pair of points (each a dict with lat and lon)."""
    global online
    est = estimate(points)
    if not online:
        return est
    coords = ";".join(f"{p['lon']:.5f},{p['lat']:.5f}" for p in points)
    try:
        r = requests.get("https://router.project-osrm.org/table/v1/driving/" + coords, timeout=10)
        r.raise_for_status()
        durations = r.json()["durations"]
        time.sleep(1)  # go easy on the free server
        # OSRM returns None for pairs it can't route (e.g. a point in a lake); keep the estimate there
        return [[e if s is None else s / 3600 for s, e in zip(row, erow)] for row, erow in zip(durations, est)]
    except Exception as error:
        print("OSRM failed, using estimates:", str(error)[:150])
        online = False
        return est
