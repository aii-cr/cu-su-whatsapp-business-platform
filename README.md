# Heimdal - User Manager Microservice AII
This is the first microservice of AII. It's a base for management of users and roles. 

## Table of Contents

- [Technologies](#technologies)
    - [Pytho Requirements](#pytho_requirements)
- [Directories Structure](#directories_structure)
- [Usage](#usage)
- [APP](#example)
- [Contributing](#app)
    - [main.py](#main.py)
    - [config.py](#config.py)
    - [API](#api)
    - [CORE](#core)
    - [DB](#db)
    - [Schema](#schema)

## Technologies

In this project, we use a FastAPI schema:
- FastAPI: is a Python API generator, it is very popular nowadays and as a backend, it is faster and more efficient than technologies such as Django and Flask.
- Mongo: is one of the most popular NoSQL databases, its structure is like json, which makes it easy to understand and with the right modules, python makes it look like dictionary management. 

### Pytho Requirements

Some of the modules are:
- email_validator==2.2.0: This module confirm that a email exist when the user register his email.
- fastapi==0.115.5: It's the main module. 
- motor==3.6.0: The mongo connector.
- pydantic==2.10.0: This module is very important because valid the data structure. 
- python-dotenv==1.0.1: Access to the .env file. 
- python-jose==3.3.0: Manage JWT tokens.

## Directories Structure
```
heimdal/
├── app/
│   ├── __init__.py
│   ├── main.py          # Entry Point
│   ├── config.py        # Configurations and global variables
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth_routes.py    # Rutas de autenticación
│   │   │   ├── user_routes.py    # Rutas de gestión de usuarios
│   │   └── dependencies.py       # Dependencies
│   ├── db/
│   │   ├── __init__.py
│   │   ├── mongo.py       # MongoDB Configuration
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── user_model.py     # User Model
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py    # Security Core
│   │   └── utils.py       # Util function
│   └── schemas/
│       ├── __init__.py
│       ├── auth_schema.py # Login/register schema
│       └── user_schema.py # User schema
├── tests/
├── venv/                  # Virtual Enveroment
├── .env                   # Enveroment Variables
├── .gitignore
├── requirements.txt       # Dependencies
├── Dockerfile             # Docker Configuration
├── docker-compose.yml
└── README.md              # Documentación
```

## APP
The app directory is the core of the project and contains the main logic. Here you organize the components of your application into modules and sub-modules to keep the code clean, modular and scalable.

### main.py
The main.py file is the main entry point of your FastAPI application. It defines and configures the application instance, registers routes and middlewares, and handles global events such as initializing and closing connections.

**Typical content:**
- FastAPI instance creation.
- Registration of routes and middlewares.
- Configuration of events such as startup and shutdown.

### config.py
The config.py file centralizes the application settings. It allows you to handle sensitive or environment-specific variables, such as database connections, secret keys and server settings.

**Typical content:**
- Configuration of variables such as DATABASE_URL, SECRET_KEY, and external service values.
- Use of Pydantic BaseSettings to load settings from environment variables.

### API
The API directory organizes the application's routes and drivers. Each file within this directory represents a set of specific routes, such as authentication, user management or logs.

**Typical content:**
- Subdirectories such as routes/ to define specific endpoints.
- Common dependencies for data injection or authentication.

### CORE
The CORE directory contains essential and reusable logic for the application. It focuses on general functionality that does not pertain directly to a specific model or controller.

**Typical content:**
- Security functions, such as password hashing and JWT token handling.
- General utilities, such as mailing or validations.

### DB
The DB directory manages the connection to the database and defines the models used in MongoDB or other databases.

**Typical contents:**
- Database connection configuration.
- Definition of models used to interact with the database.

**Important subdirectories:**
- mongo.py: Configures the connection to MongoDB and manages events such as initialization or closing.
- models/: Defines the models used in the database

### Schema
The schemas directory defines the Pydantic schemas used to validate and structure the data sent or received through the API.

**Typical content:**
- Validation schemas for endpoint inputs and outputs.
- Data structures for automatic API documentation.

**Common files:**
- auth_schema.py: Schemas for registration and login.
- log_schema.py: Schemas for creating and updating logs.
