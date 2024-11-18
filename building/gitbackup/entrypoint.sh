#!/bin/bash
set -e

# Craete log file
touch /var/log/cron.log

# Schedule execution: adjust the timing as needed
echo "${CRON} root cd ${GITBACKUP_DIR} && curl https://api.github.com/users/${GITHUB_USER}/starred | jq -r '.[].html_url' | xargs -l git clone > /var/log/cron.log 2>&1" > /etc/cron.d/gitbackup

# Apply cron job and start cron service
chmod 0644 /etc/cron.d/gitbackup
crontab /etc/cron.d/gitbackup
cron

# Keep the container running
tail -f /var/log/cron.log