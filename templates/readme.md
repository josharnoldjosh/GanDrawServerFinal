## install
`pip3 install -r requirements.txt --user`

## launch server
`gunicorn --worker-class eventlet -w 1 app:app`