# MEX - MultiChain Explorer

*A lightweight MultiChain Explorer*

**NOTE: Work in progress**

## Development Setup

This project requires python 3.6, postgres and a MultiChain node with RPC 
access for local development and testing.

Install dependencies in your virtual env with `pip install -r requirements.txt`
Create your configuration in `mex/settings/config.py` (see `sample_config.py`).
Get up and running with these commands:

```
python manage.py makemigrations mex
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit the admin interface at http://127.0.0.0:8000/admin/ and login with
the credentials you created. To start syncing the blockchain execute 
`python -m mex.sync`


## Roadmap to first release

- [x] Minimal datamodel for blocks, transactions, inputs, outputs and addresses
- [x] Synchronization of blockchain data via JSON-RPC
- [ ] Minimal REST api for webfrontend with node bridge/proxy
- [ ] Web Frontend
- [ ] Deployment scripts
