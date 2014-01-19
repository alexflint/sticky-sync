#!/bin/bash
gunicorn --daemon --timeout 1000 --bind 0.0.0.0:5000 server:app
