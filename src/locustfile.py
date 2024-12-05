from locust import HttpUser, TaskSet, task, between

# TODO: non funziona, still da capire

class UserBehavior(TaskSet):
    def on_start(self):
        self.register()
        self.login()

    def register(self):
        response = self.client.post("/auth/register", json={
            "username": "testuser",
            "password": "testpassword",
            "email": "testuser@example.com",
            "role": "normalUser"
        })
        if response.status_code != 200:
            print(f"Registration failed with status code {response.status_code}")

    def login(self):
        response = self.client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpassword"
        })
        self.headers = {}  # Initialize headers
        if response.status_code == 200:
            try:
                print(response.json())
                self.token = response.json()["access_token"]
                self.user_id = response.json()["userID"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
            except KeyError:
                print("Login failed: 'access_token' not found in response")
        else:
            print(f"Login failed with status code {response.status_code}")
            

    @task(1)
    def increase_balance(self):
        self.client.get("/user/increase_balance", headers=self.headers, json={"userID": self.user_id, "amount": 10000})
        
    @task(2)
    def roll_gatcha(self):
        for _ in range(1000):
            response = self.client.get("/gatcha/roll", headers=self.headers)
            if response.status_code == 200:
                gatcha_id = response.json()["gatcha"]["_id"]
                self.add_gatcha_to_collection(gatcha_id)

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 5)