# ASE_Project

Advanced Software Engineering 24/25 Course Project

## Get Started

1. Navigate to the src folder:
   
   ```shell
   cd ASE_Project/src
   ```

2. Build and start the services using Docker Compose:
   
   ```shell
   docker compose up --build
   ```

3. Navigate to the **root** folder (important):
   
   ```shell
   cd ..
   ```

4. Run the integration tests collection using Newman:
   
   ```shell
   newman run docs/integration-tests.postman_collection.json -e docs/localhost-ema-with-https.postman_environment.json --insecure
   ```


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

3. Navigate to the **root** folder (important):
   
   ```shell
   cd ..
   ```

4. Run the isolation tests collection using Newman:
   
   ```shell
   newman run docs/isolation-auth-service.postman_collection.json -e docs/localhost-ema-with-https.postman_environment.json --insecure
   newman run docs/isolation-gatcha-service.postman_collection.json -e docs/localhost-ema-with-https.postman_environment.json --insecure
   newman run docs/isolation-market-service.postman_collection.json -e docs/localhost-ema-with-https.postman_environment.json --insecure
   newman run docs/isolation-user-service.postman_collection.json -e docs/localhost-ema-with-https.postman_environment.json --insecure
   ```

5. Use the browser client on localhost:8080

## The /docs folder

Contains:

- architecture.yml: the architecture diagram exported from MicroFreshner, can be imported into the web app to view the architecture.
- Gaga OpenAPI.yml: the openAPI specification, importable in Swagger to check the REST API endpoint specification.
- ASE Report.pdf: the detailed report of the project.
- locustfile.py: locust python script for performance and rolling probabilities tests.
- The Postman collections and environment for integration and isolation testing.
- A test.jpg image, used by the Postman tests.
