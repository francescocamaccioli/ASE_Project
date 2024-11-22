# ASE_Project

Advanced Software Engineering 24/25 Course Project

- [Postman Workspace](https://elements.getpostman.com/redirect?entityId=26720283-80745346-aaa6-4cff-b0dd-137edb46a5f3&entityType=collection) with tests

## Getting Started

The project is based on 5 microservices:

1. DataBase Manager: handles the data stored inside the 3 DBs (Gatcha - User - Market)
2. Gatcha: handles the interaction of users with gatchas
3. Gateway: forwards incoming HTTP requests to the appropriate microservice
4. Market: handles auctions and bidding functionalities
5. User: handles the interaction of users and admins with their profiles in the application

## How to run the project

feature/market
- execute the `docker compose up --build` command from the `src` directory
- use any browser to use the following endpoints:
  - localhost:5001/

1. Navigate to the src folder:
    ```sh
    cd ASE_Project/src
    ```

2. Build and start the services using Docker Compose:
    ```sh
    docker compose up --build
    ```


## The /docs folder

Contains:
- architecture.yml: the architecture diagram exported from MicroFreshner, can be imported into the web app to view the architecture

TODO:
- pdf report
- openapi
- export postman collection
- locust file
- copy of github actions workflow