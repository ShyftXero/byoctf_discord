DISCORD_TOKEN = "nope"

USER_TOKEN = "nope"


flask_secret_key = "nope"

#elephantsql.com

postgres_db_type = "postgres"  # sqlite is easy and works well enough. I probably won't leverage the others.; that being said, hosted cockroach or postgres is also easy...
postgres_db_host = '1.2.3.4'
# postgres_db_host = "drone.db.elephantsql.com"  # database host
postgres_db_port = 5432
postgres_db_user = "usernaem"  # db username
postgres_db_pass = "your_password"  # db password
postgres_db_database = "db_name_here"


#google oauth
google_client_id = "nope"
google_client_secret = "nope"

# digitalocean

# postgres_db_type = "postgres"  # sqlite is easy and works well enough. I probably won't leverage the others.; that being said, hosted cockroach or postgres is also easy...
# postgres_db_host = '64.227.0.211'
# # postgres_db_host = "db-postgresql-nyc1-00473-do-user-2771432-0.b.db.ondigitalocean.com"  # database host
# postgres_db_port = 25060
# postgres_db_user = "doadmin"  # db username
# postgres_db_pass = "your_password"  # db password
# postgres_db_database = "defaultdb"



#cockroach.cloud serverless

cockroach_db_type = "cockroach"  # sqlite is easy and works well enough. I probably won't leverage the others.; that being said, hosted cockroach or postgres is also easy...
cockroach_db_host = 'dusk-panther-13723.5xj.cockroachlabs.cloud'
# cockroach_db_host = '35.184.49.11'
cockroach_db_port = 26257
cockroach_db_user = "your_user"  # db username
cockroach_db_pass = "your_password"  # db password
cockroach_db_database = "defaultdb"

#ca cert needed for cockroachlabs
#curl --create-dirs -o $HOME/.postgresql/root.crt 'https://cockroachlabs.cloud/clusters/b212fbc6-3812-478b-9d0e-e4263ecbad2a/cert'


#export DATABASE_URL="postgresql://your_user:REVEAL_PASSWORD@dusk-panther-13723.5xj.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full"
