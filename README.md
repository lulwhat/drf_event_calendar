## DRF application for managing events

### Features:
+ Creating and managing events
+ Tagging events
+ Various filters and text search
+ Booking seats for events
+ Rating visited events
+ Background tasks for notifying attendees

### Stack: 
+ Python 3.12.2
+ Django REST Framework 3.16.0
+ PostgreSQL 17.5
+ Celery 5.5.2
+ Redis 5.3.0
+ gRPC
+ Nginx

<br/>

Prepared to deploy with Docker-compose

Full list of requirements: [requirements.txt](/app/requirements.txt)

Full task description for the API: [task_description.docx](/task_description.docx)

<br/>

**Note:** By default DB is prepopulated with test data by [generate_initial_data](/app/fixtures/generate_initial_data.py) script -- if you want a clean DB after deployment, change GENERATE_INITIAL_DATA parameter to False in [.env](.env)

<br/><br/>


### To use locally run following steps:

**Build containers:** `docker-compose up --build -d`

Check containers are up and running: `docker ps -a`

Access Swagger UI: <http://localhost/api/docs/>

Authentication is managed with JWT tokens. Access `/api/login` endpoint for Token issuance and use it in `Authorize`

Admin credentials: `admin admin`

Test users credentials: `user_{1-10} password123`

**Shutdown the app:** `docker-compose down -v --remove-orphans`

#### Optional:

Admin panel: <http://localhost/admin/>

Run autotests: `docker exec -it web pytest -v`

Monitor Celery tasks with flower: <http://localhost:5555/>
