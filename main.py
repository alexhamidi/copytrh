import time

import robin_stocks.robinhood as rh

from constants import (
    CIK,
    ROBINHOOD_ACCOUNT_NUMBER,
    ROBINHOOD_PASSWORD,
    ROBINHOOD_USERNAME,
)
from data import get_positions


def order_summary(approved: list[tuple[str, float, float]]) -> str:
    total = sum(a for _, a, _ in approved)
    sep = "─" * 40
    lines = [f"\n{sep}", f"  {'Ticker':<8} {'Amount':>8}  {'Weight':>7}", sep]
    for ticker, amount, weight in approved:
        lines.append(f"  {ticker:<8} ${amount:>7.2f}  {weight:>6.1%}")
    lines += [sep, f"  {'TOTAL':<8} ${total:>7.2f}", sep]
    return "\n".join(lines)


def main():
    rh.login(ROBINHOOD_USERNAME, ROBINHOOD_PASSWORD)

    amount_to_invest = float(input("How much to invest ($)? ").strip())

    positions = get_positions(cik=CIK, include_options=False)

    # Step 1: approve each position individually
    approved = []
    for ticker, weight in positions:
        amount = int(weight * amount_to_invest * 100) / 100
        confirm = input(f"Include {ticker} — ${amount:.2f} ({weight:.1%})? [y/N] ").strip().lower()
        if confirm == "y":
            approved.append((ticker, amount, weight))

    if not approved:
        print("Nothing approved.")
        rh.logout()
        return

    # Step 2: summary + final confirmation
    print(order_summary(approved))

    final = input("\nPlace all orders? [y/N] ").strip().lower()
    if final != "y":
        print("Cancelled.")
        rh.logout()
        return

    # Step 3: validate tickers before placing any orders
    print("\nValidating tickers...")
    valid_approved = []
    for ticker, amount, weight in approved:
        quote = rh.get_latest_price(ticker)
        if not quote or quote[0] is None:
            print(f"  {ticker}: skipped (not found on Robinhood)")
        else:
            valid_approved.append((ticker, amount, weight))

    if not valid_approved:
        print("No valid tickers to order.")
        rh.logout()
        return

    if len(valid_approved) < len(approved):
        skipped = len(approved) - len(valid_approved)
        confirm2 = input(f"\n{skipped} ticker(s) skipped. Proceed with {len(valid_approved)} orders? [y/N] ").strip().lower()
        if confirm2 != "y":
            print("Cancelled.")
            rh.logout()
            return

    # Step 4: execute with delay to avoid rate limiting
    for ticker, amount, _ in valid_approved:
        order = rh.order_buy_fractional_by_price(
            ticker,
            amountInDollars=amount,
            account_number=ROBINHOOD_ACCOUNT_NUMBER,
            timeInForce="gfd",
        )
        if order and "non_field_errors" in order:
            print(f"{ticker}: FAILED — {order['non_field_errors'][0]}")
        elif order is None:
            print(f"{ticker}: FAILED — rate limited or no response")
        else:
            print(f"{ticker}: queued ({order.get('state', '?')})")
        time.sleep(3)

    rh.logout()


if __name__ == "__main__":
    main()
