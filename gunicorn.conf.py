# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "unix:/var/www/visaguardai/visaguardai.sock"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/var/www/visaguardai/logs/gunicorn_access.log"
errorlog = "/var/www/visaguardai/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "visaguardai"

# Server mechanics
preload_app = True
daemon = False
pidfile = "/var/www/visaguardai/visaguardai.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (if needed)
keyfile = None
certfile = None

