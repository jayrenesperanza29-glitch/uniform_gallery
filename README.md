# Uniform Gallery

A full-stack web application for browsing and managing school uniforms. Students can register, log in, and view the uniform catalog with size-based pricing. Admins can create, update, and delete uniforms, manage prices, and upload images.

---

## Tech Stack

| Layer     | Technology                                      |
|-----------|-------------------------------------------------|
| Frontend  | React + Vite, React Router, plain CSS           |
| Backend   | Python / Flask, PyJWT, Werkzeug, psycopg2       |
| Database  | PostgreSQL 16                                   |
| Images    | Local `/static/images/` (dev) or Cloudinary     |
| Container | Docker + Docker Compose                         |
| Deploy    | Render (backend: Python web service, frontend: static site) |

---

## API Reference

All endpoints are prefixed with `/api`.

### Auth

| Method | Endpoint          | Auth     | Description              |
|--------|-------------------|----------|--------------------------|
| POST   | `/auth/register`  | Public   | Register a student        |
| POST   | `/auth/login`     | Public   | Log in (returns JWT)      |
| GET    | `/auth/me`        | JWT      | Get current user info     |

### Uniforms

| Method | Endpoint            | Auth     | Description              |
|--------|---------------------|----------|--------------------------|
| GET    | `/uniforms`         | JWT      | List all uniforms        |
| GET    | `/uniforms/:id`     | JWT      | Get a single uniform     |

### Admin

| Method | Endpoint                    | Auth     | Description              |
|--------|-----------------------------|----------|--------------------------|
| POST   | `/admin/uniforms`           | Admin    | Create a uniform         |
| PUT    | `/admin/uniforms/:id`       | Admin    | Update a uniform         |
| DELETE | `/admin/uniforms/:id`       | Admin    | Delete a uniform         |
| POST   | `/admin/prices`             | Admin    | Add a price entry        |
| PUT    | `/admin/prices/:id`         | Admin    | Update a price entry     |
| DELETE | `/admin/prices/:id`         | Admin    | Delete a price entry     |
| GET    | `/admin/students`           | Admin    | List all students        |
| POST   | `/admin/upload`             | Admin    | Upload a uniform image   |

### Other

| Method | Endpoint              | Description           |
|--------|-----------------------|-----------------------|
| GET    | `/api/health`         | Health check          |
| GET    | `/static/images/:file`| Serve local images    |

---

## Database Schema

```
student    — student_id, student_name, email, password, created_at
admin      — admin_id, admin_name, email, password
uniform    — uniform_id, uniform_type, description, image_path
price      — price_id, uniform_id (FK), label, amount
```

Prices cascade-delete when a uniform is deleted.

---

## License

This project is for internal school use.
