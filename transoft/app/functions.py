import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


def format_invoice_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y.%m.%d")
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        return date_str


def format_order_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
        return date_obj
    except ValueError:
        return date_str


def get_invoice_info(text):
    pattern = re.compile(
        r"(\d{8})\s+\d+\s+\d+\s+(\d{4}\.\d{2}\.\d{2}).*?Date of shipment:\s+(\d{4}\.\d{2}\.\d{2}).*?(\d{4}/\d{3}/\d{4}).*?Total\s+([\d,.]+)\s+EUR",
        re.IGNORECASE | re.DOTALL
    )
    match = pattern.search(text)

    if not match:
        return None

    invoice_no = match.group(1)
    invoice_date = format_invoice_date(match.group(2))
    position = match.group(4)
    amount_str = match.group(5).replace(" EUR", "").strip()

    try:
        freight_value = float(Decimal(amount_str.replace(",", ".")))
    except (InvalidOperation, ValueError):
        freight_value = 0.0

    return {
        "invoice_no": invoice_no,
        "invoice_date": invoice_date,
        "position": position,
        "freight_value": freight_value
    }


def find_vehicle(text):
    match = re.search(r'Vehicle:\s*(DEAB[A-Z0-9]*)', text)
    if match:
        return match.group(1)
    return None


def get_order_info(text):
    pattern = re.compile(r"""
        (?P<DateA>\d{2}\.\d{2}\.\d{4})\s+\w\s+(?P<Position>\d{4}/\d{3}/\d{4})\s+(?P<Trailer>[A-Z0-9]+)\s+(?P<Amount>\d{1,3},\d{2})\s*\n
        (?P<DepartureA>[^\n]+)\n
        (?P<ArrivalA>[^\n]+)
        |
        (?P<DateB>\d{2}\.\d{2}\.\d{4})\s+\w(?:\s+\*?[A-Z0-9]*)?\s*\n
        (?P<DepartureB>[^\n]+)\n
        (?P<ArrivalB>[^\n]+)
        """, re.VERBOSE)

    vehicle_match = re.search(r'Vehicle:\s*(DEAB[A-Z0-9]*)', text)
    vehicle = vehicle_match.group(1) if vehicle_match else None

    results = []
    for match in pattern.finditer(text):
        if match.group("DateA"):
            amount_str = match.group("Amount").replace(",", ".")
            try:
                amount = float(amount_str)
            except ValueError:
                amount = 0.0
            results.append({
                "order_date": format_order_date(match.group("DateA")),
                "position": match.group("Position"),
                "trailer": match.group("Trailer"),
                "amount": amount,
                "departure": match.group("DepartureA").strip(),
                "arrival": match.group("ArrivalA").strip(),
                "vehicle": vehicle,
            })
        elif match.group("DateB"):
            results.append({
                "order_date": format_order_date(match.group("DateB")),
                "position": "-",
                "trailer": "-",
                "amount": 0,
                "departure": match.group("DepartureB").strip(),
                "arrival": match.group("ArrivalB").strip(),
                "vehicle": vehicle,
            })
    return results if results else None
