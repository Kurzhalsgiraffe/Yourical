mv instance/database.db ..
git stash & git pull
mv ../database.db instance/database.db
systemctl restart untis_to_ical.service
