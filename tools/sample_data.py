from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

CITIES = [
    "São Paulo",
    "Rio de Janeiro",
    "Belo Horizonte",
    "Curitiba",
    "Recife",
    "Salvador",
    "Porto Alegre",
    "Brasília",
    "Campinas",
    "Goiânia",
]
CUISINES = [
    "Brasileira",
    "Japonesa",
    "Pizza",
    "Hambúrguer",
    "Mexicana",
    "Árabe",
    "Doce",
    "Saudável",
    "Italiana",
    "Indiana",
]
RESTAURANTS = {
    "Brasileira": ["Sabor da Casa", "Mineiro Express", "Feijão & Cia"],
    "Japonesa": ["Sushi Bar 7", "Nikkei Go", "Wasabi Fast"],
    "Pizza": ["Forno Noturno", "Napoli 30min", "Pizza da Esquina"],
    "Hambúrguer": ["Smash House", "Burger Lab", "Pão & Fogo"],
    "Mexicana": ["Taco Livre", "Guaca-Guaca", "El Paso Delivery"],
    "Árabe": ["Esfiha do Zé", "Sahara Express", "Hommous & Cia"],
    "Doce": ["Doce Hora", "Açaí do Parque", "Churros & Shake"],
    "Saudável": ["Green Bowl", "Fit Box", "Salada Urbana"],
    "Italiana": ["Nonna Pasta", "Al Dente", "Cantina 12"],
    "Indiana": ["Masala Express", "Curry Box", "Taj Delivery"],
}
STATUSES = ["delivered", "delivered", "delivered", "delivered", "late", "cancelled"]
PAYMENTS = ["pix", "credit", "credit", "debit", "voucher"]


def generate_orders(n: int = 800, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    start = datetime(2026, 1, 5, 11, 0, 0)
    rows: list[dict] = []
    for i in range(1, n + 1):
        cuisine = rng.choice(CUISINES)
        city = rng.choices(CITIES, weights=[22, 14, 10, 8, 7, 8, 7, 9, 8, 7], k=1)[0]
        status = rng.choice(STATUSES)
        hour = rng.choice([11, 12, 12, 13, 18, 19, 19, 20, 21])
        day = start + timedelta(days=rng.randint(0, 260), hours=0)
        dt = day.replace(hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59))
        value = round(rng.lognormvariate(3.6, 0.45), 2)
        fee = round(rng.choice([0.0, 4.99, 6.99, 8.99, 11.99]), 2)
        if status == "cancelled":
            delivery_time = ""
            rating = ""
        else:
            base = rng.randint(18, 55)
            delivery_time = base + (20 if status == "late" else 0)
            rating = rng.choice([3, 4, 4, 5, 5, 5]) if rng.random() > 0.12 else ""
        rows.append(
            {
                "order_id": f"IF{i:05d}",
                "order_datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "city": city,
                "restaurant": rng.choice(RESTAURANTS[cuisine]),
                "cuisine": cuisine,
                "order_value": value,
                "delivery_fee": fee,
                "delivery_time_min": delivery_time,
                "status": status,
                "payment_method": rng.choice(PAYMENTS),
                "rating": rating,
            }
        )
    return rows


def write_sample_csv(dest: str | Path, n: int = 800, seed: int = 42) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_orders(n=n, seed=seed)
    fieldnames = list(rows[0].keys())
    with dest.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return dest


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "data" / "raw" / "pedidos_ifood.csv"
    path = write_sample_csv(out)
    print(f"escrito {path}")
