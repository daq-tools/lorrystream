docker inspect --format "{{json .State.Health }}" <container name> | jq '.Log[].Output' | tac

https://stackoverflow.com/questions/42737957/how-to-view-docker-compose-healthcheck-logs
