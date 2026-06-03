# DIAToolkit

Distributional Impact Analysis: Toolkit

A RESTful API built with Flask that provides endpoints for managing and accessing application data.


## Project Team

This project was developed as a collaborative effort by the following team members:

| Name               | Role         |
|--------------------|--------------|
| Sonia Gonzalez     | Data science |
| Juan Felipe Jurado | Data science |
| Sebastian Sanchez  | Developer    |

### Responsibilities

* **Data science:** Schema design, data modeling, and database integration.
* **Data science:** Schema design, data modeling, and database integration.
* **Developer:** Project setup, API documentation, and maintenance guides.

## Features

* REST API architecture
* JSON request and response handling
* Environment-based configuration
* Error handling and validation
* Easy deployment and scalability

## Requirements

* Python 3.9+
* pip

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd <project-folder>
```

2. Create and activate a virtual environment:

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

## Running the Application

```bash
flask run
```

The API will be available at:

```text
http://127.0.0.1:5000
```

## API Endpoints

| Method | Endpoint           | Description     |
| ------ | ------------------ | --------------- |
| GET    | /                  | Health check    |
| GET    | /api/resource      | Get resources   |
| POST   | /api/resource      | Create resource |
| PUT    | /api/resource/<id> | Update resource |
| DELETE | /api/resource/<id> | Delete resource |

## Example Request

```bash
curl -X GET http://127.0.0.1:5000/api/resource
```

## Testing

```bash
pytest
```

## Project Structure

```text
project/
├── app.py
├── requirements.txt
├── .env
├── routes/
├── services/
├── models/
├── tests/
└── README.md
```

