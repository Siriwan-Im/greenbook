# Greenbook

Greenbook is a Django-based web application for used vehicle price prediction using Machine Learning models.

## Features

* Vehicle price prediction
* Django web application
* Machine Learning model integration
* Vehicle information management
* Historical auction data analysis
* Model training and deployment

---

## Technology Stack

### Backend

* Python 3.11+
* Django

### Machine Learning

* Scikit-Learn
* XGBoost
* LightGBM
* CatBoost

### Frontend

* HTML
* CSS
* Bootstrap
* JavaScript

---

## Project Structure

```text
greenbook/
│
├── data/
├── datascientist/
├── greenbook/
├── manage.py
├── requirements.txt
├── import_asset_sold_car.py
├── import_greenbook.py
└── test_data.py
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/Siriwan-Im/greenbook.git
cd greenbook
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

Windows

```bash
venv\Scripts\activate
```

Mac / Linux

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Database Migration

```bash
python manage.py migrate
```

---

## Run Development Server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000
```

---

## Machine Learning Features

* Vehicle price prediction
* Brand-specific models
* Time-series market analysis
* Feature engineering
* Model evaluation and comparison
* Automated prediction workflow

---

## Environment Variables

Create a `.env` file:

```env
SECRET_KEY=your_secret_key
DEBUG=True

DB_SERVER=your_server
DB_DATABASE=your_database
DB_USERNAME=your_username
DB_PASSWORD=your_password
```

---

## Requirements

* Python 3.11+
* Git
* SQL Server (Optional)
* ODBC Driver 17/18 for SQL Server

---

## Deployment

The project can be deployed on:

* Windows Server
* Linux Server
* Cloud VM
* Docker (Optional)

---

## Author

**Siriwan Imumphai**
