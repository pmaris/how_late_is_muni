Application for tracking the arrival times for all San Francisco Muni transit route using the NextBus API, for determining the on-time performance of every route on a stop-by-stop basis.

This project is a complete refactor from the ground up of a project I previously worked on in 2013 and 2014. Currently, the half of the application for monitoring and storing arrivals is in progress. Once that is completed, the next half will be to build a website (Using Django) for presenting the results, including daily on-time performance calculations on each stop on every route, and aggregations of data over time and along entire routes.

Getting started
---

### Dependencies
First, install prerequisites:
- PostgreSQL
- Python >= 3.6
- Pip

### Setup
1. In Postgres, create the `muni` database and `muni` user, with a password of your choosing.
2. Create a [`.pgpass` file](https://www.postgresql.org/docs/9.3/libpq-pgpass.html) in `$HOME/.pgpass`. Use a wildcard (`*`) for the database name, `muni` for the username, and the password you chose. For example: `*:*:*:muni:<your password>`
3. Install project dependencies: `pip3 install -r requirements.txt`
4. Create the database tables: `python3 manage.py migrate`
5. Add the current schedules to the database: `python3 manage.py update_schedules`

### Running the worker
You can run the worker with the command `python3 manage.py run`

Commands
---
Currently, the following commands are supported with `manage.py`:

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
