import signal
from src.helpers import colors as c

def signal_handler(sig, frame):
    c.p('\n[r]Exit.')
    exit(130)

signal.signal(signal.SIGINT, signal_handler)
