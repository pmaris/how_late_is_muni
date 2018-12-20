Application for tracking the arrival times for all San Francisco Muni transit route using the NextBus API, for determining the on-time performance of every route on a stop-by-stop basis

Getting started
---

### Dependencies
First, install Docker:
1. Install [Docker CE](https://docs.docker.com/install/)
2. Install [Docker Compose](https://docs.docker.com/compose/install/)

### Setup
1. Set a password for the database by editing the `db_config.env` file and setting a value for the `POSTGRES_PASSWORD` key.
2. Build the Docker containers using the command `docker-compose build`
3. Bring up the **database** Docker container using the command `docker-compose up database`
4. Create the required tables in the database from the **worker** Docker container using the command `docker-compose run worker python manage.py migrate`
5. Add schedules to the database from the **worker** Docker container using the command `docker-compose run worker python manage.py update_schedules`

### Running the worker
The worker will automatically run when the **worker** Docker container is brought up. Start it by using the command `docker-compose up worker`

Commands
---
Currently, the following worker commands are supported with Django's `manage.py`:

### Update schedules
Update the schedules stored in the database, for either all routes or only a single route.

**Command:**

`python3 <repository path>/manage.py update_schedules`

**Arguments:**

- `--route <route tag>`: Update the schedules for the indicated route instead of for all routes.

### Run
Run the worker to track and add arrivals to the database, for either all routes or only a single route.

**Command:**

`python3 <repository path>/manage.py run`

**Arguments:**

- `--route <route tag>`: Track arrivals for the indicated route instead of for all routes.
