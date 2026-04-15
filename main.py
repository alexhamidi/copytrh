import robin_stocks.robinhood as rh

from constants import (
    CIK,
    ROBINHOOD_ACCOUNT_NUMBER,
    ROBINHOOD_PASSWORD,
    ROBINHOOD_USERNAME,
)
from data import get_positions


def main():
    rh.login(ROBINHOOD_USERNAME, ROBINHOOD_PASSWORD)

    amount_to_invest = float(input("How much to invest ($)? ").strip())

    positions = get_positions(cik=CIK, include_options=False)

    # Step 1: approve each position individually
    approved = []
    for ticker, weight in positions:
        amount = round(weight * amount_to_invest, 2)
        confirm = input(f"Include {ticker} — ${amount:.2f} ({weight:.1%})? [y/N] ").strip().lower()
        if confirm == "y":
            approved.append((ticker, amount, weight))

    if not approved:
        print("Nothing approved.")
        rh.logout()
        return

    # Step 2: summary + final confirmation
    total = sum(a for _, a, _ in approved)
    print(f"\n{'─' * 40}")
    print(f"  {'Ticker':<8} {'Amount':>8}  {'Weight':>7}")
    print(f"{'─' * 40}")
    for ticker, amount, weight in approved:
        print(f"  {ticker:<8} ${amount:>7.2f}  {weight:>6.1%}")
    print(f"{'─' * 40}")
    print(f"  {'TOTAL':<8} ${total:>7.2f}")
    print(f"{'─' * 40}")

    final = input("\nPlace all orders? [y/N] ").strip().lower()
    if final != "y":
        print("Cancelled.")
        rh.logout()
        return

    # Step 3: execute
    for ticker, amount, _ in approved:
        order = rh.order_buy_fractional_by_price(
            ticker,
            amountInDollars=amount,
            account_number=ROBINHOOD_ACCOUNT_NUMBER,
            timeInForce="gfd",
        )
        print(f"{ticker}: {order}")

    rh.logout()


if __name__ == "__main__":
    main()
