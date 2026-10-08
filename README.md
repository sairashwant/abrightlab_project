# Peazy Margin Lab

Why do some of 2,000 cleaning locations lose money, and what fixes it? All data is synthetic.

**Live demo:** _paste your link here_

## Files

- `config.json`: every input (cities, wages, assumptions, planted problems, plan defaults). In production, Peazy's database replaces this and the synthetic generator.
- `model.py`: builds the network, diagnoses each location, makes territories and routes, and writes `index.html`.
- `road.py`: drive times from OpenStreetMap (OSRM). No account needed.
- `template.html`: the dashboard.
- `app.py`: serves the dashboard and rebuilds it when you click **Refresh drive times**.

## Run

```bash
pip install -r requirements.txt
python app.py     # first start builds the model (about 5 minutes), then open http://127.0.0.1:5000
```

## AI tools used

_Edit so it accurately describes what you did._ I used Claude (Anthropic) as a coding assistant. I chose the approach and assumptions, and reviewed and tested the results.
