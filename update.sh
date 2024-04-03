mv instance/database.db ..
git stash & git pull
mv ../database.db instance/database.db
docker compose build
docker compose up -d