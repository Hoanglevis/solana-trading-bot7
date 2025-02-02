import requests
from solana.rpc.api import Client
from solana.transaction import Transaction, TransactionInstruction
from solana.system_program import TransferParams, transfer
from solana.publickey import PublicKey
from solana.keypair import Keypair
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import transfer as spl_transfer
import time

# Setup Solana Client and Payer (private key for signing transactions)
client = Client("https://api.mainnet-beta.solana.com")
payer = Keypair()  # Replace with your actual wallet's Keypair

# Replace with the token you want to buy (e.g., USDC)
token_address = PublicKey("TOKEN_ADDRESS")  # Replace with the token address
amount_in_sol = 1  # Amount to buy in SOL (1 SOL)
slippage = 0.15  # Slippage set to 15%
moonbag_percentage = 0.15  # 15% moonbag (will not be sold)
priority_fee = 20000  # Example priority fee in lamports
known_rug_pullers = [
    "known_rugger_address_1", "known_rugger_address_2", "known_rugger_address_3"
]  # Replace with actual addresses

# Function to check contract score from SolSniffer API
def check_contract_score(contract_address):
    api_key = "YOUR_API_KEY"
    solsniffer_base_url = "https://api.solsniffer.com/check_contract"
    url = f"{solsniffer_base_url}?contract_address={contract_address}&apikey={api_key}"

    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        contract_score = data.get("score", None)
        return contract_score
    return None

# Function to check if the contract score is below 85
def is_contract_safe(contract_address):
    score = check_contract_score(contract_address)
    if score is not None and score < 85:
        print(f"Warning: Contract score for {contract_address} is {score}, which is below the safe threshold.")
        return False
    return True

# Function to check for fake volume
def is_fake_volume(volume, average_volume):
    if volume > (average_volume * 10):
        print(f"Warning: Volume of {volume} is suspiciously high compared to the average volume of {average_volume}.")
        return True
    return False

# Function to check if the token is associated with known rug-pullers
def is_known_rug_puller(contract_address):
    if contract_address in known_rug_pullers:
        print(f"Warning: Token with address {contract_address} is associated with a known rug-puller.")
        return True
    return False

# Function to calculate the amount of tokens to buy
def calculate_buy_amount(token_price_in_sol, amount_in_sol, slippage):
    amount_to_buy = (amount_in_sol / token_price_in_sol) * (1 + slippage)
    return amount_to_buy

# Function to execute a buy
def execute_buy(token_address, amount_in_sol, slippage, moonbag_percentage):
    # Example price per token in SOL (fetch this dynamically from a price source)
    token_price_in_sol = 0.1  # Placeholder: You should use an API to fetch live prices
    
    # Calculate amount to buy
    amount_to_buy = calculate_buy_amount(token_price_in_sol, amount_in_sol, slippage)
    print(f"Buying {amount_to_buy} tokens with {amount_in_sol} SOL.")

    # Prepare transaction for buying the token
    transaction = Transaction()

    transaction.add(
        spl_transfer(
            source=payer.public_key,
            dest=token_address,
            owner=payer,
            amount=int(amount_to_buy),
            program_id=TOKEN_PROGRAM_ID
        )
    )

    # Send transaction with priority fee
    response = client.send_transaction(transaction, payer)
    print(f"Buy transaction sent: {response}")

    # Moonbag to hold (leave 15% of tokens unsold)
    moonbag_amount = amount_to_buy * moonbag_percentage
    print(f"Moonbag to hold: {moonbag_amount} tokens")

    return response

# Function to execute a sell
def execute_sell(token_address, amount_in_token, moonbag_percentage, bought_price_in_sol, current_price_in_sol):
    price_increase_factor = current_price_in_sol / bought_price_in_sol
    
    if price_increase_factor >= 10:
        amount_to_sell = amount_in_token * 0.85  # Sell 85% of holdings
        print(f"Price increased by {price_increase_factor}x. Selling {amount_to_sell} tokens.")

        # Prepare transaction to transfer tokens back
        transaction = Transaction()
        transaction.add(
            spl_transfer(
                source=payer.public_key,
                dest=token_address,
                owner=payer,
                amount=int(amount_to_sell),
                program_id=TOKEN_PROGRAM_ID
            )
        )

        # Send the sell transaction with priority fee
        response = client.send_transaction(transaction, payer)
        print(f"Sell transaction sent: {response}")

        return response
    else:
        print("Price hasn't reached 10x, holding position.")
        return None

# Function to send a transaction with a priority fee
def send_transaction_with_priority_fee(transaction, payer, priority_fee):
    transaction.fee_payer = payer.public_key
    transaction.recent_blockhash = client.get_recent_blockhash()['result']['value']['blockhash']

    transaction.instructions.append(
        TransactionInstruction(
            keys=[{"pubkey": payer.public_key, "is_signer": True, "is_writable": True}],
            program_id=PublicKey("FeeProgramPublicKey"),
            data=priority_fee.to_bytes(8, 'little')  # Priority fee in lamports
        )
    )

    response = client.send_transaction(transaction, payer)
    print(f"Transaction with priority fee sent: {response}")
    return response

# Example usage:
token_address = PublicKey("TOKEN_ADDRESS")  # Replace with token address
amount_in_sol = 1  # 1 SOL buy amount
slippage = 0.15  # 15% slippage
moonbag_percentage = 0.15  # 15% moonbag

# Step 1: Execute Buy
response = execute_buy(token_address, amount_in_sol, slippage, moonbag_percentage)

# Step 2: Simulate Sell (Assuming you have the amount and token data)
amount_in_token = 1000  # Example: amount of tokens you bought
bought_price_in_sol = 0.1  # Example: the price at which you bought the token
current_price_in_sol = 1  # Example: the current price of the token
response = execute_sell(token_address, amount_in_token, moonbag_percentage, bought_price_in_sol, current_price_in_sol)

