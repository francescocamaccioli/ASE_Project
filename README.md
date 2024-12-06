# ASE_Project

Advanced Software Engineering 24/25 Course Project

- [Postman Workspace](https://elements.getpostman.com/redirect?entityId=26720283-80745346-aaa6-4cff-b0dd-137edb46a5f3&entityType=collection) with tests

## Get Started

1. Navigate to the src folder:
   
   ```shell
   cd ASE_Project/src
   ```

2. Build and start the services using Docker Compose:
   
   ```shell
   docker compose up --build
   ```

3. Use Postman to run the *integration-tests* Collection.

## Isolation Testing

To test each microservice in isolation, run the following steps:

1. Navigate to the chosen microservice directory (auth/gatcha/market/user):
   
   ```shell
   cd ASE_Project/src/<microservice directory>
   ```

2. Build and start the service in isolation using Docker Compose:
   
   ```shell
   docker compose up --build
   ```

3. Use Postman to run the isolation test collection related to the chosen microservice

## The /docs folder

Contains:

- architecture.yml: the architecture diagram exported from MicroFreshner, can be imported into the web app to view the architecture.
- Gaga OpenAPI.yml: the openAPI specification, importable in Swagger to check the REST API endpoint specification.
- ASE Report.pdf: the detailed report of the project.
- locustfile.py: locust python script for performance and rolling probabilities tests.