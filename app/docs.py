#!/usr/bin/env python3

"""This module add documentation to app."""

docs = """
# Hospital Backend System API Documentation

Author: [Maxwell Nana Forson](https://www.mnforson.live)

Source Code: <https://github.com/nanafox/hospital_backend_system>

## Overview
The **Hospital Backend System API** is a backend system designed to facilitate
secure and structured note-sharing between doctors and their patients.
It provides authentication, role-based access control (RBAC), secure
storage of medical notes, and background task processing to manage follow-ups and reminders.

## Core Features
- **Secure Authentication & Authorization** using JWT-based OAuth2.
- **Role-Based Access Control (RBAC)** where doctors and patients have distinct privileges.
- **Encrypted Notes Storage** to ensure confidentiality of medical data.
- **Doctor-Patient Association** allowing access to notes only for authorized users.
- **Background Task Processing** to manage actionable steps via Celery and Redis.
- **Comprehensive API Testing** ensuring reliability and correctness.

---
## System Design Choices

### **1. FastAPI as the Backend Framework**
- FastAPI was chosen for its speed, asynchronous capabilities, automatic
  OpenAPI documentation, and built-in data validation using Pydantic.
- It is highly efficient and well-suited for handling concurrent requests,
  making it a great choice for real-time applications.

### **2. SQLAlchemy for Database ORM**
- SQLAlchemy provides a robust ORM that integrates well with relational databases.
- The current implementation can work with any database backend, such as MySQL,
  PostgreSQL or SQLite. We are using **Postgres**.

### **3. Role-Based Access Control (RBAC)**
- Doctors and Patients have different permissions:
  - **Doctors** can create and view notes for their assigned patients.
  - **Patients** can only view their own notes.
- Access is controlled through dependencies that check user roles before
  allowing operations.

### **4. Secure Notes Storage with Encryption**
- Notes are stored in an encrypted format using **Fernet symmetric encryption**
  to ensure data confidentiality.
- Even if the database is compromised, the sensitive medical data remains
  unreadable without decryption keys.

### **5. Celery & Redis for Background Tasks**
- Certain tasks, like **sending reminders or managing follow-ups**, are executed
  asynchronously using Celery.
- Redis serves as the message broker for Celery, ensuring fast and reliable
  task queuing.

---
## Authentication & Authorization

### **OAuth2 with JWT**
- The API implements OAuth2 password flow, where users authenticate and receive
  a JWT access token.
- **Access Tokens** are used to authorize API requests.
- Tokens have a limited lifespan, requiring periodic refreshes.

---
## API Endpoints

### **1. Authentication**
| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/api/v1/auth/signup` | Register a new user (doctor or patient) |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain access token |
| `GET`  | `/api/v1/auth/me` | Retrieve logged-in user details |
| `PUT`  | `/api/v1/auth/me` | Update logged-in user profile |
| `POST` | `/api/v1/auth/logout` | Log out current user |

### **2. Doctor Profile Management**
| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET`  | `/api/v1/me/profile` | Retrieve logged-in doctor’s profile |
| `PUT`  | `/api/v1/me/profile` | Update logged-in doctor’s profile |

### **3. Patient-Doctor Selection**
| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET`  | `/api/v1/doctors` | List all available doctors |
| `POST` | `/api/v1/me/doctors` | Select doctors as a patient |
| `POST` | `/api/v1/me/doctors/remove` | Remove selected doctors as a patient |
| `GET`  | `/api/v1/me/doctors` | Retrieve patient’s selected doctors |
| `GET`  | `/api/v1/me/patients` | Retrieve list of patients assigned to the doctor |

### **4. Doctor Notes**
| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/api/v1/notes` | Submit a new doctor’s note for a patient |
| `GET`  | `/api/v1/notes?patient_id={patient_id}` | Retrieve all notes for a patient |
| `GET`  | `/api/v1/notes?doctor_id={doctor_id}` | Retrieve all notes from a doctor |

### **5. Actionable Steps & Reminders**
| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET`  | `/api/v1/me/actionable-steps` | Retrieve actionable steps for logged-in user |
| `GET`  | `/api/v1/patients/{patient_id}/actionable-steps` | Retrieve actionable steps for a patient |
| `GET`  | `/api/v1/patients/{patient_id}/actionable-steps/complete` | Mark step as complete for a patient |

---
## Background Task Processing (Celery & Redis)
- The system uses Celery to handle **asynchronous background tasks**,
  such as notifying patients when a doctor submits a note.
- Redis serves as the message broker, ensuring fast and reliable task execution.
- Once a note is submitted, the system queues a task to generate actionable
  steps and send reminders to the patient.
  - The actionable steps are intelligently generated by a trained AI model.

---
## Testing & Mock Data

### **Testing Frameworks Used**
- **pytest**: For unit and integration tests.
- **HTTPX**: For API test requests.

---
## Conclusion
This API provides a **secure and scalable** solution for doctor-patient
interactions, ensuring efficient management of medical notes and follow-ups.
It is built with a focus on security, performance, and usability. 🚀
"""
