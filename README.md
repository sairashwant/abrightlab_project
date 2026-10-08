# Peazy Margin Lab

A prototype for the **abrightlab 2,000-Location Challenge**, by Sai Rashwant Venkataraman Sundaram.

**[Live dashboard](https://sairashwant.github.io/abrightlab_project/)** | **[Full write-up (PDF)](Sai_abrightlab_Challenge_Writeup.pdf)**

## Summary

Losing locations aren't one problem, so negotiating vendor prices across the board won't fix them. Each location loses money for a specific, measurable reason that Peazy's data already reveals, and each reason has its own fix.

This prototype diagnoses all 2,000 locations, redesigns vendor territories and routes, and tests a recovery plan before it touches a customer:

- **Diagnosis:** each location's gap to its 25% target margin splits into four causes: underpricing, travel and low density, unpaid scope creep, and billed hours above geofence time. The biggest one is its cause.
- **Territories and routes:** K-Means groups each metro's sites into territories served by one vendor, and 2-opt builds each route from real OpenStreetMap drive times.
- **Plan simulator:** estimates each fix per location and tests any combination.

## Results (synthetic data)

| | Today | With the plan |
|---|---|---|
| Locations losing money | 612 | 138 |
| Gross margin | 5.5% | 17.4% |

In New York, 7 vendors crisscrossing the city become 24 territory routes with 63% less driving.

## Run it locally

```bash
pip install -r requirements.txt
python app.py     # first start takes about 5 minutes, then open http://127.0.0.1:5000
```

| File | Purpose |
|---|---|
| `config.json` | All inputs and assumptions |
| `model.py` | Diagnosis, territories, routes, and dashboard build |
| `road.py` | Drive times from OpenStreetMap (OSRM), no account needed |
| `template.html` | Dashboard |
| `app.py` | Flask server with a one-click rebuild |

Built with Python, scikit-learn, OSRM, and Flask. All data is synthetic; see the write-up for assumptions, limitations, and AI tools used.
