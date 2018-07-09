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
