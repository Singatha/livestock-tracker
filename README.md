# Livestock Tracker

A system for tracking and monitoring livestock.


## Run Locally

Clone the project

```bash
  git clone https://github.com/Singatha/livestock-tracker.git
```


To run the project, go to the project folder

```bash
  cd livestock-tracker
```
and run

```bash
  docker-compose up --build
```

To compose down run

```bash
  docker-compose down
```

To compose down run and remove images

```bash
  docker-compose down --rmi all
```

To compose down run, remove images and volumes

```bash
  docker-compose down -v --rmi all
```
## Authors

- [@singatha](https://www.github.com/singatha)

## Roadmap

- Adding endpoints
- Error handling
- Authentication
- Caching
- Security

frontend
   |
   |
api gateway -- ml-service
| | | |
| | | rabbitmq (email service)
| | keycloak (auth)
| livestock tracker service

livestock_id
user_id
group_name
livestock_type
health_status
age
expected_growth
created_at
updated_at

python -m grpc_tools.protoc -I../../protos --python_out=. --pyi_out=. --grpc_python_out=. ../../protos/route_guide.proto
protoc -I=$SRC_DIR --python_out=$DST_DIR $SRC_DIR/addressbook.proto

python3 -m grpc_tools.protoc -I=../livestock-tracker-protos --python_out=../livestock-tracker-protos/ --grpc_python_out=../livestock-tracker-protos ../livestock-tracker-protos/livestock.proto
