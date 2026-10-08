"""Peazy Margin Lab: why do locations lose money, and what fixes it? Inputs live in config.json."""
import json
import math
import random

import numpy as np
from sklearn.cluster import KMeans

import road

C = json.load(open("config.json"))
P = C["planted_problems"]


def make_network():
    """Synthetic stand-in for Peazy's location, vendor and contract data."""
    vendors, sites = [], []
    for m, metro in enumerate(C["metros"]):
        for _ in range(2 + metro["size"] // 2):
            vendors.append({
                "metro": m, "lat": metro["lat"] + random.gauss(0, 0.08), "lon": metro["lon"] + random.gauss(0, 0.08),
                "rate": metro["wage"] * random.uniform(0.95, 1.1),
                "padding": random.uniform(1.08, 1.25) if random.random() < P["overbilling_vendors"] else 1,
            })
    for i in range(C["locations"]):
        m = random.choices(range(len(C["metros"])), [x["size"] for x in C["metros"]])[0]
        metro = C["metros"][m]
        remote = random.random() < P["remote_sites"]
        if remote:  # small town 30-100 miles out
            a, d = random.uniform(0, 2 * math.pi), random.uniform(0.4, 1.4)
            lat, lon = metro["lat"] + d * math.sin(a), metro["lon"] + d * math.cos(a)
        else:
            spread = 0.05 + 0.012 * metro["size"]
            lat, lon = metro["lat"] + random.gauss(0, spread), metro["lon"] + random.gauss(0, spread * 1.2)
        sites.append({
            "id": f"L{i:04d}", "metro": m, "lat": lat, "lon": lon, "remote": remote, "wage": metro["wage"],
            "vendor": random.choice([j for j, v in enumerate(vendors) if v["metro"] == m]),
            "sqft": random.randrange(*C["sqft_range"], 100),
            "visits": random.choice(C["visits_per_week"]) * 4.33,  # per month
            "price_factor": random.uniform(0.7, 0.86) if random.random() < P["underpriced_contracts"] else random.gauss(1, 0.05),
            "scope": random.uniform(1.2, 1.45) if random.random() < P["scope_creep"] else 1,
        })
    return vendors, sites


def add_drive_times(vendors, sites):
    """Drive hours from each site to its vendor, from OpenStreetMap in batches of 90."""
    for m, metro in enumerate(C["metros"]):
        print(f"Drive times {m + 1}/{len(C['metros'])}: {metro['name']}")
        vs = [j for j, v in enumerate(vendors) if v["metro"] == m]
        ss = [s for s in sites if s["metro"] == m]
        for i in range(0, len(ss), 90):
            batch = ss[i:i + 90]
            table = road.drive_hours([vendors[j] for j in vs] + batch)
            for k, s in enumerate(batch):
                s["drive"] = table[vs.index(s["vendor"])][len(vs) + k]


def diagnose(s, v):
    """Split the gap to target margin into four causes; the biggest one is the cause."""
    hours = s["sqft"] / C["sqft_per_hour"]   # contracted hours per visit
    onsite = hours * s["scope"]              # geofence hours
    billed = onsite * v["padding"]           # invoiced hours
    s["travel"] = s["drive"] * (v["rate"] + C["vehicle_cost_per_hour"])
    price = s["visits"] * (hours * s["wage"] + C["priced_travel_per_visit"]) / (1 - C["target_margin"])
    s.update(rate=v["rate"], hours=round(hours, 1), onsite=round(onsite, 1), billed=round(billed, 1),
             revenue=price * s["price_factor"], cost=s["visits"] * (billed * v["rate"] + s["travel"]))
    s["gaps"] = [price - s["revenue"],
                 s["visits"] * (s["travel"] - C["priced_travel_per_visit"]),
                 s["visits"] * hours * (s["scope"] - 1) * v["rate"],
                 s["visits"] * (billed - onsite) * v["rate"]]
    s["cause"] = s["gaps"].index(max(s["gaps"])) if s["revenue"] < s["cost"] else None


def route(t):
    """Nearest neighbour, then 2-opt. t is a drive-time table; stop 0 is the vendor."""
    order, left = [0], set(range(1, len(t)))
    while left:
        order.append(min(left, key=lambda j: t[order[-1]][j]))
        left.remove(order[-1])
    order.append(0)
    length = lambda o: sum(t[a][b] for a, b in zip(o, o[1:]))
    improved = True
    while improved:
        improved = False
        for i in range(1, len(order) - 2):
            for k in range(i + 1, len(order) - 1):
                new = order[:i] + order[i:k + 1][::-1] + order[k + 1:]
                if length(new) < length(order):
                    order, improved = new, True
    return order, length(order)


def make_territories(vendors, sites):
    """K-Means groups each metro into territories, each served by one of its most honest vendors."""
    territories = []
    for m, metro in enumerate(C["metros"]):
        print(f"Routes {m + 1}/{len(C['metros'])}: {metro['name']}")
        ss = [s for s in sites if s["metro"] == m and not s["remote"]]
        labels = KMeans(n_clusters=round(len(ss) / C["sites_per_territory"])).fit_predict([[s["lon"], s["lat"]] for s in ss])
        best = sorted((v for v in vendors if v["metro"] == m), key=lambda v: v["padding"])[:3]
        for c in set(labels):
            members = [s for s, label in zip(ss, labels) if label == c]
            v = best[c % len(best)]
            stops = [v] + members
            order, hours = route(road.drive_hours(stops))
            per_visit = hours / len(members) * (v["rate"] + C["vehicle_cost_per_hour"])
            for s in members:
                s["consolidate"] = max(0, s["visits"] * (s["travel"] - per_visit))
            territories.append({
                "metro": m, "path": [[round(stops[o]["lat"], 4), round(stops[o]["lon"], 4)] for o in order],
                "before": sum(s["drive"] * s["visits"] for s in members),
                "after": hours / len(members) * sum(s["visits"] for s in members),
            })
    return territories


def fixes(s):
    """Monthly value of each fix for this site."""
    under, _, scope, billing = s["gaps"]
    local = s["visits"] * (s["travel"] - C["priced_travel_per_visit"] - C["local_vendor_premium"] * s["billed"] * s["rate"])
    return {"reprice": max(0, under), "change_order": max(0, scope) / (1 - C["target_margin"]),
            "verified_hours": max(0, billing), "consolidate": s.get("consolidate", 0),
            "local_vendor": max(0, local) if s["remote"] else 0}


def check(sites):
    """Share of planted problems the diagnosis finds."""
    losing = [s for s in sites if s["cause"] is not None and not s["remote"]]
    under = [s for s in losing if s["price_factor"] < 0.9 and s["scope"] == 1]
    scope = [s for s in losing if s["scope"] > 1 and s["price_factor"] >= 0.9]
    return [round(sum(s["cause"] == 0 for s in under) / len(under), 2),
            round(sum(s["cause"] == 2 for s in scope) / len(scope), 2)]


def build():
    """Run every step and write index.html."""
    random.seed(7)
    np.random.seed(7)
    road.online = True
    vendors, sites = make_network()
    add_drive_times(vendors, sites)
    for s in sites:
        diagnose(s, vendors[s["vendor"]])
    territories = make_territories(vendors, sites)

    data = {
        "osrm": road.online, "check": check(sites), "causes": C["causes"], "plan": C["plan"],
        "target_margin": C["target_margin"], "metros": [m["name"] for m in C["metros"]],
        "vendors": [[round(v["lat"], 4), round(v["lon"], 4)] for v in vendors], "territories": territories,
        "sites": [{"id": s["id"], "metro": s["metro"], "lat": round(s["lat"], 4), "lon": round(s["lon"], 4),
                   "remote": s["remote"], "vendor": s["vendor"], "sqft": s["sqft"], "hours": s["hours"],
                   "onsite": s["onsite"], "billed": s["billed"], "revenue": round(s["revenue"]),
                   "cost": round(s["cost"]), "cause": s["cause"],
                   "fixes": {k: round(v) for k, v in fixes(s).items()}} for s in sites],
    }
    open("index.html", "w").write(open("template.html").read().replace("/*DATA*/", json.dumps(data)))
    print(f"Done: {sum(s['revenue'] < s['cost'] for s in sites)} losing locations, OSRM used: {road.online}")


if __name__ == "__main__":
    build()
