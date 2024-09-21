### start.sh
bash
#!/bin/bash

# Start Gunicorn in the background
gunicorn app:app --bind 0.0.0.0:8000 &

# Start your bot
python bot.py

# Wait for background processes to finish
wait
