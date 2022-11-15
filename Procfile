primary:./bin/litefs -config ./etc/primary.yml
secondary1:./bin/litefs -config ./etc/secondary1.yml
secondary2:./bin/litefs -config ./etc/secondary2.yml

games-api: hypercorn games-api --reload --debug --bind games-api.local.gd:8000 --access-logfile - --error-logfile - --log-level DEBUG
