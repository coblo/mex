# MEX - MultiChain Explorer

*A lightweight MultiChain Explorer*

**NOTE: Work in progress**

## Development Setup

This project requires python 3, postgres and a MultiChain node with RPC 
access for local development and testing.

It is recommended to use a python virtualenv for development.
Install dependencies in your activated virtualenv with 
`pip install -r requirements.txt`. Create your configuration in 
`mex/settings/config.py` (see `sample_config.py`). Get your development 
environment up and running with these commands:

```
fab reset
python -m mex.sync
python manage.py runserver
```

If you make changes to the django models you can simply run `fab reset` and
it will create a fresh database reflecting your new models. But be aware to
**only ever use `fab reset` for development** because it will:

- **delete and recreate** django migration files
- **drop and recreate** a database named `mex`
- create a demo superuser (user: admin, password: admin)


`python -m mex.sync` starts a separate background process that will synchronize 
the database with the node.

After starting your the app with `python manage.py runserver` visit the admin 
interface at http://127.0.0.0:8000/admin/ and login with the the credentials
shown by the output of `fab reset`.


## Roadmap to first release

- [x] Minimal datamodel for blocks, transactions, inputs, outputs and addresses
- [x] Synchronization of blockchain data via JSON-RPC
- [ ] Minimal REST api for webfrontend with node bridge/proxy
- [ ] Web Frontend
- [ ] Deployment scripts
