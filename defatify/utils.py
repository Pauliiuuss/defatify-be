from decimal import Decimal, ROUND_HALF_UP

def convert_kg_to_lb(value_in_kg):
    pounds = value_in_kg * Decimal(2.20462)
    return pounds.quantize(Decimal('0.0'), rounding=ROUND_HALF_UP)