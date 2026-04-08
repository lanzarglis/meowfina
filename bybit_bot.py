python
#!/usr/bin/env python3
from pybit.http import HttpSession
import os

API_KEY = os.getenv("BYBIT_API_KEY", "Pv6AlB3a6hp4lYG7uPHl")
API_SECRET = os.getenv("BYBIT_API_SECRET", "r9qhlWicesztsfyf4pMq8nPDM0tp3ohgfqg")

session = HttpSession(
    testnet=False,
    api_key=API_KEY,
    api_secret=API_SECRET
)

try:
    result = session.get_wallet_balance(accountType="UNIFIED")
    print("Balance:", result)
except Exception as e:
    print("Error:", e)
