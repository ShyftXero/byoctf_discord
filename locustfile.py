from locust import HttpUser, between, task
from locust.contrib.fasthttp import FastHttpUser

import random

import database as db
with db.db_session:
    chall_uuids = db.select(s.uuid for s in db.Challenge)[:]
    user_api_keys = db.select(u.api_key for u in db.User)[:]

class WebsiteUser(FastHttpUser):
    wait_time = between(1, 2)
    
    
    @task
    def index(self):
        self.client.get("/")
        
    @task
    def about(self):
        self.client.get("/hud")

    @task
    def about(self):
        self.client.get(f"/hud/{random.choice(user_api_keys)}")

    @task
    def about(self):
        self.client.get("/hud/transactions")

    @task
    def about(self):
        self.client.get(f"/chall/{random.choice(chall_uuids)}")


    # @task
    # def search(self):
    #     terms = ['hacking', '%20', 'iteration', 'loop', 'bool', 'robotics', 'impacts', 'switch' ]
    #     self.client.get(f'/api/v1/search?query={random.choice(terms)}')
