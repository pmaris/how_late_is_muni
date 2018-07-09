Application for tracking the arrival times for all San Francisco Muni transit route using the NextBus API, for determining the on-time performance of every route on a stop-by-stop basis.

This project is a complete refactor from the ground up of a project I previously worked on in 2013 and 2014. Currently, the half of the application for monitoring and storing arrivals is in progress. Once that is completed, the next half will be to build a website (Using Django) for presenting the results, including daily on-time performance calculations on each stop on every route, and aggregations of data over time and along entire routes.

Getting started
---
First, install prerequisites:
- MySQL server
- Python >= 3.6
- Pip

Then, install dependencies with the command `pip install -r <repository path>/requirements.txt`

Commands
---
Currently, the following commands are supported with `manage.py`:

### Update schedules
Update the schedules stored in the database, for either all routes or only a single route.

**Command:**

`python <repository path>/manage.py update_schedules`

**Arguments:**

- `--route <route tag>`: Update the schedules for the indicated route instead of for all routes.

### Run
Run the worker to track and add arrivals to the database, for either all routes or only a single route.

**Command:**

`python <repository path>/manage.py run`

**Arguments:**

- `--route <route tag>`: Track arrivals for the indicated route instead of for all routes.
