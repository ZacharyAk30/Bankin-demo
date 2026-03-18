from __future__ import annotations

import argparse
import random
import string
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from bankin_platform.config import settings
from infra.s3_local import S3Local


@dataclass(frozen=True)
class RawTransaction:
    transaction_id: str
    user_id: str
    amount: float  # negative = dépense, positive = revenu
    currency: str
    label: str  # libellé brut banque
    booking_date: str  # ISO date
    created_at: str  # ISO datetime
    category: str  # vérité terrain (pour entraînement & monitoring)


_CATEGORIES = [
    "groceries",
    "restaurants",
    "transport",
    "rent",
    "utilities",
    "salary",
    "shopping",
    "subscriptions",
    "health",
    "travel",
    "cash_withdrawal",
    "fees",
    "insurance",
]

# Paires (merchant,label templates, category, typical amount range)
_MERCHANTS: list[tuple[str, list[str], str, tuple[float, float]]] = [
    ("CARREFOUR", ["CARREFOUR CITY {city}", "CB CARREFOUR {city}"], "groceries", (-120, -8)),
    ("LECLERC", ["E.LECLERC {city}", "CB LECLERC {city}"], "groceries", (-150, -10)),
    ("UBER", ["UBER TRIP {city}", "UBER *TRIP {city}"], "transport", (-45, -6)),
    ("SNCF", ["SNCF VOYAGES {city}", "BILLET SNCF {city}"], "transport", (-180, -12)),
    ("RATP", ["RATP NAVIGO {city}", "CB RATP {city}"], "transport", (-95, -20)),
    ("NETFLIX", ["NETFLIX.COM", "NETFLIX *SUBSCRIPTION"], "subscriptions", (-20, -8)),
    ("SPOTIFY", ["SPOTIFY ABONNEMENT", "SPOTIFY *PREMIUM"], "subscriptions", (-20, -8)),
    ("AMAZON", ["AMAZON EU *{rand}", "AMZN Mktp FR *{rand}"], "shopping", (-250, -8)),
    ("ZARA", ["ZARA {city}", "ZARA FR {city}"], "shopping", (-200, -15)),
    ("IKEA", ["IKEA {city}", "CB IKEA {city}"], "shopping", (-500, -20)),
    ("EDF", ["EDF FACTURE", "PRELEV EDF"], "utilities", (-200, -30)),
    ("ORANGE", ["ORANGE FACTURE", "PRELEV ORANGE"], "utilities", (-120, -15)),
    ("LOYER", ["LOYER {city}", "VIR LOYER {city}"], "rent", (-1500, -600)),
    ("SALAIRE", ["VIR SALAIRE {company}", "SALAIRE {company}"], "salary", (1500, 5500)),
    ("DOCTOLIB", ["DOCTOLIB {city}", "CB DOCTOLIB {city}"], "health", (-80, -20)),
    ("PHARMACIE", ["PHARMACIE {city}", "CB PHARMACIE {city}"], "health", (-60, -8)),
    ("AIRFRANCE", ["AIR FRANCE {rand}", "AIRFRANCE {rand}"], "travel", (-800, -60)),
    ("ATM", ["RETRAIT DAB {city}", "RETRAIT ATM {city}"], "cash_withdrawal", (-200, -20)),
    ("FRAIS", ["FRAIS TENUE COMPTE", "COMMISSION INTERVENTION"], "fees", (-30, -5)),
    ("AXA", ["PRELEV AXA ASSURANCE", "AXA ASSURANCE"], "insurance", (-150, -20)),
]

_CITIES = ["PARIS", "LYON", "MARSEILLE", "LILLE", "NANTES", "TOULOUSE", "BORDEAUX"]
_COMPANIES = ["ACME SAS", "INNOTECH", "FINTECH FR", "DATA CORP"]


def _rand_id(prefix: str, n: int = 12) -> str:
    return prefix + "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def _render_template(tpl: str) -> str:
    return tpl.format(
        city=random.choice(_CITIES),
        company=random.choice(_COMPANIES),
        rand="".join(random.choices(string.ascii_uppercase + string.digits, k=6)),
    )


def _sample_amount(amount_range: tuple[float, float]) -> float:
    lo, hi = amount_range
    # légère asymétrie (beaucoup de petits montants, quelques gros)
    u = random.random() ** 2
    return round(lo + (hi - lo) * u, 2)


def generate_transactions(n_users: int, n_tx: int, start_date: date, days: int) -> list[RawTransaction]:
    users = [f"u_{i:05d}" for i in range(1, n_users + 1)]
    txs: list[RawTransaction] = []
    for _ in range(n_tx):
        merchant, templates, category, amount_range = random.choice(_MERCHANTS)
        label = _render_template(random.choice(templates))
        booking = start_date + timedelta(days=random.randint(0, days - 1))
        created = datetime.now(timezone.utc).isoformat()

        txs.append(
            RawTransaction(
                transaction_id=_rand_id("tx"),
                user_id=random.choice(users),
                amount=_sample_amount(amount_range),
                currency="EUR",
                label=label,
                booking_date=booking.isoformat(),
                created_at=created,
                category=category,
            )
        )
    return txs


def write_to_s3_local(txs: list[RawTransaction], root: str) -> Path:
    s3 = S3Local(Path(root))
    bucket = "raw"

    # Partitionnement type S3: transactions/booking_date=YYYY-MM-DD/part-*.jsonl
    by_date: dict[str, list[dict]] = {}
    for t in txs:
        by_date.setdefault(t.booking_date, []).append(asdict(t))

    last_path: Path | None = None
    for d, rows in sorted(by_date.items()):
        key = f"transactions/booking_date={d}/part-00000.jsonl"
        last_path = s3.put_jsonl(bucket=bucket, key=key, rows=rows)
    assert last_path is not None
    return last_path


def main() -> None:
    p = argparse.ArgumentParser(description="Generate raw banking transactions (JSONL) into S3-like lake.")
    p.add_argument("--n-users", type=int, default=200)
    p.add_argument("--n-tx", type=int, default=20000)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--start-date", type=str, default=str(date.today() - timedelta(days=30)))
    p.add_argument("--s3-root", type=str, default=settings.s3_local_root)
    args = p.parse_args()

    random.seed(args.seed)
    start = date.fromisoformat(args.start_date)

    txs = generate_transactions(args.n_users, args.n_tx, start_date=start, days=args.days)
    last = write_to_s3_local(txs, root=args.s3_root)
    print(f"Wrote {len(txs)} transactions. Last file: {last}")


if __name__ == "__main__":
    main()

