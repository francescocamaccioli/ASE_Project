# locustfile.py
from locust import FastHttpUser, task, between, events
import random
import string
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GachaUser(FastHttpUser):
    wait_time = between(1, 3)  # Wait time between tasks

    # Shared rarity counts and lock for thread safety
    rarity_counts = {"comune": 0, "raro": 0, "epico": 0, "leggendario": 0}
    rarity_counts_lock = threading.Lock()

    # Shared list of auction IDs
    auction_ids = []
    auction_details = {}  # Define as class attribute
    auction_ids_lock = threading.Lock()

    def on_start(self):
        """Initialize user by performing health check, registration, login, and balance increase."""
        try:
            self.perform_health_check()
            self.register_user()
            self.login_user()
            self.increase_balance(100000)
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.environment.runner.quit()

    def perform_health_check(self):
        """Perform a health check to ensure the API Gateway is running."""
        response = self.client.get("/", verify=False)
        if response.status_code == 200:
            logger.info("Health check passed: API Gateway is running.")
        else:
            logger.error(f"Health check failed with status code: {response.status_code}")
            raise Exception("Health check failed.")
    
    # --- Auth Microservice Tasks ---

    def register_user(self):
        """Register a new user."""
        self.username = 'user_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        response = self.client.post(
            "/auth/register",
            json={
                "username": self.username,
                "password": self.password,
                "email": f"{self.username}@example.com",
                "role": "normalUser"
            },
            verify=False
        )
        if response.status_code == 200:
            logger.info(f"Registration successful for {self.username}")
        else:
            logger.error(f"Registration failed for {self.username}: {response.status_code} - {response.text}")
            raise Exception("Registration failed.")

    def login_user(self):
        """Log in the registered user to obtain authentication token."""
        response = self.client.post(
            "/auth/login",
            json={
                "username": self.username,
                "password": self.password
            },
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token", "")
            self.user_id = data.get("userID", "")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            logger.info(f"Login successful for {self.username}")
        else:
            logger.error(f"Login failed for {self.username}: {response.status_code} - {response.text}")
            raise Exception("Login failed.")

    def increase_balance(self, amount):
        """Increase user balance to facilitate gacha operations."""
        response = self.client.post(
            "/user/increase_balance",
            headers=self.headers,
            json={"userID": self.user_id, "amount": amount},
            verify=False
        )
        if response.status_code == 200:
            self.balance = amount
            logger.info(f"Balance increased by {amount} for {self.username}.")
        else:
            logger.error(f"Failed to increase balance for {self.username}: {response.status_code} - {response.text}")
            raise Exception("Increase balance failed.")

    # --- User Microservice Tasks ---

    @task(1)
    def get_balance(self):
        """Retrieve user balance."""
        if not self.token:
            return
        response = self.client.get("/user/balance", headers=self.headers, verify=False)
        if response.status_code == 200:
            balance = response.json().get("balance", 0)
            self.balance = balance  # Update local balance
            logger.info(f"{self.username} has a balance of {balance}.")
        else:
            logger.error(f"Failed to retrieve balance for {self.username}: {response.status_code} - {response.text}")

    @task(2)
    def view_inventory(self):
        """View user inventory."""
        response = self.client.get(f"/user/collection", headers=self.headers, verify=False)
        if response.status_code == 200:
            self.inventory = response.json()  # Assuming the response is a list
            logger.info(f"{self.username} viewed their inventory. Items: {self.inventory}")
        else:
            logger.error(f"Failed to retrieve inventory for {self.username}: {response.status_code} - {response.text}")

    # --- Gatcha Microservice Tasks ---

    @task(5)
    def roll_gacha(self):
        """Simulate rolling the gacha."""
        if self.balance < 10:
            logger.info(f"{self.username} does not have enough balance to roll the gacha.")
            return

        response = self.client.get("/gatcha/roll", headers=self.headers, verify=False)
        if response.status_code == 200:
            data = response.json()
            gacha = data.get("gatcha", {})
            rarity = gacha.get("rarity", "unknown")
            item_id = gacha.get("gatcha_uuid")
            self.balance -= 10
            with GachaUser.rarity_counts_lock:
                if rarity in GachaUser.rarity_counts:
                    GachaUser.rarity_counts[rarity] += 1
                else:
                    GachaUser.rarity_counts[rarity] = 1

            if item_id:
                logger.info(f"{self.username} rolled a {rarity} item: {item_id}")
        else:
            logger.error(f"Gacha roll failed for {self.username}: {response.status_code} - {response.text}")

    @task(1)
    def get_all_gatchas(self):
        """Retrieve all gatchas."""
        response = self.client.get("/gatcha/gatchas", headers=self.headers, verify=False)
        if response.status_code == 200:
            gatchas = response.json()
            logger.info(f"{self.username} retrieved all gatchas.")
        else:
            logger.error(f"Failed to retrieve all gatchas for {self.username}: {response.status_code} - {response.text}")

    @task(1)
    def get_gatcha_details(self):
        """Retrieve details of a specific gatcha."""
        response = self.client.get("/gatcha/gatchas", headers=self.headers, verify=False)
        if response.status_code == 200:
            gatchas = response.json()
            if gatchas:
                gatcha_id = random.choice(gatchas)['_id']
                response = self.client.get(f"/gatcha/gatchas/{gatcha_id}", headers=self.headers, verify=False)
                if response.status_code == 200:
                    gatcha = response.json()
                    logger.info(f"{self.username} retrieved gatcha {gatcha_id}.")
                else:
                    logger.error(f"Failed to retrieve gatcha {gatcha_id} for {self.username}: {response.status_code} - {response.text}")
            else:
                logger.info(f"{self.username} has no gatchas to retrieve.")
        else:
            logger.error(f"Failed to retrieve gatchas for {self.username}: {response.status_code} - {response.text}")

    # --- Market Microservice Tasks ---

    @task(1)
    def add_auction(self):
        """Add a new auction."""
        if not hasattr(self, 'inventory') or not self.inventory:
            logger.info(f"{self.username} has no items to auction.")
            return

        gatcha_id = random.choice(self.inventory)
        # Remove the item from the inventory
        self.inventory.remove(gatcha_id)
        starting_price = random.randint(100, 1000)

        response = self.client.post(
            "/market/add-auction",
            headers=self.headers,
            json={
                "Gatcha_ID": gatcha_id,
                "starting_price": starting_price
            },
            verify=False
        )
        if response.status_code == 201:
            logger.info(f"{self.username} added an auction for item {gatcha_id} with starting price {starting_price}.")
        else:
            logger.error(f"Failed to add auction for {self.username}: {response.status_code} + {response.text}")

    @task(2)
    def place_bid(self):
        """Place a bid on an auction."""
        with GachaUser.auction_ids_lock:
            if not GachaUser.auction_ids:
                logger.info("No auction IDs available to place a bid.")
                return
            auction_id = random.choice(GachaUser.auction_ids)

        # Fetch the latest auction details to get the most recent current_price
        response_details = self.client.get(
            "/market/auction",
            headers=self.headers,
            json={"Auction_ID": auction_id},  # Sending JSON body as per server expectation
            verify=False
        )

        if response_details.status_code != 200:
            # Extract error message from the response
            error_message = response_details.json().get("error", response_details.text)
            logger.error(f"Failed to fetch auction {auction_id} details: {error_message}")
            return

        auction = response_details.json()

        # Ensure the user does not bid on their own auctions
        if auction.get("Auctioner_ID") == self.user_id:
            logger.info(f"{self.username} cannot bid on their own auction {auction_id}.")
            return

        # Ensure the bid amount is higher than the current highest bid
        try:
            current_price = int(auction.get("current_price", 0))
        except (ValueError, TypeError):
            logger.error(f"Invalid current_price for auction {auction_id}: {auction.get('current_price')}")
            return

        # Define the bid amount to be higher than current_price
        bid_amount = random.randint(current_price + 1, current_price + 1000)
        logger.info(f"{self.username} attempting to bid {bid_amount} on auction {auction_id} with current_price {current_price}")

        # Check if the user has sufficient balance
        if bid_amount > self.balance:
            logger.info(f"{self.username} does not have enough balance to place a bid of {bid_amount}. Current balance: {self.balance}")
            return

        # Place the bid
        response = self.client.post(
            "/market/bid",
            headers=self.headers,
            json={
                "Auction_ID": auction_id,
                "amount": bid_amount
            },
            verify=False
        )

        if response.status_code == 200:
            self.balance -= bid_amount
            with GachaUser.auction_ids_lock:
                GachaUser.auction_details[auction_id]["current_price"] = bid_amount
            logger.info(f"{self.username} placed a bid of {bid_amount} on auction {auction_id}. New balance: {self.balance}")
        elif response.status_code == 400:
            # Extract and log the specific error message
            error_message = response_details.json().get("error", response_details.text)
            logger.info(f"{self.username} failed to place a bid on auction {auction_id}: {error_message}")
        else:
            logger.error(f"Failed to place bid on auction due to service failure {auction_id} for {self.username}: {response.status_code} - {response.text}")

    @task(1)
    def get_auction(self):
        """Get details of a specific auction."""
        with GachaUser.auction_ids_lock:
            if GachaUser.auction_ids:
                auction_id = random.choice(GachaUser.auction_ids)
            else:
                logger.info("No auction IDs available to retrieve details.")
                return

        response = self.client.get(
            f"/market/auction",
            headers=self.headers,
            json={"Auction_ID": auction_id},
            verify=False
        )
        if response.status_code == 200:
            logger.info(f"{self.username} retrieved details for auction {auction_id}.")
        else:
            logger.error(f"Failed to retrieve details for auction {auction_id} for {self.username}: {response.status_code} - {response.text}")

    @task(1)
    def get_all_auctions(self):
        """Get all active auctions."""
        response = self.client.get("/market/auctions", headers=self.headers, verify=False)
        if response.status_code == 200:
            auctions = response.json()  # Assuming the response is a list
            with GachaUser.auction_ids_lock:
                GachaUser.auction_ids.clear()
                GachaUser.auction_details.clear()
                GachaUser.auction_ids.extend([auction["Auction_ID"] for auction in auctions])
                GachaUser.auction_details.update({auction["Auction_ID"]: auction for auction in auctions})
            logger.info(f"{self.username} retrieved all active auctions.")
        else:
            logger.error(f"Failed to retrieve all active auctions for {self.username}: {response.status_code} - {response.text}")

# Event listener to print rarity counts after the test
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n=== Rarity Counts ===")
    total_rolls = sum(GachaUser.rarity_counts.values())
    if total_rolls == 0:
        print("No gacha rolls were performed.")
    else:
        for rarity, count in GachaUser.rarity_counts.items():
            percentage = (count / total_rolls) * 100 if total_rolls > 0 else 0
            print(f"{rarity.capitalize()}: {count} rolls ({percentage:.2f}%)")
    print("=====================\n")