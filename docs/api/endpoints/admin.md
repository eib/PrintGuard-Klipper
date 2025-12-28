# Admin API

Admin endpoints for managing users, machine-to-machine (M2M) applications, and system-wide settings.

## Auth

- Requires an **access token** in `Authorization: Bearer ...`
- All endpoints require **`admin`** scope

## Endpoints

### Users

- `POST /api/admin/users`: Create a user
  - **Body**

    ```json
    {
      "username": "alice",
      "password": "optional (omit to auto-generate)",
      "scopes": "printer:read printer:write rtc:stream"
    }
    ```

  - **Response**: returns `password` only when it was auto-generated.

- `GET /api/admin/users`: List users
- `DELETE /api/admin/users/{username}`: Delete a user

### M2M applications

- `POST /api/admin/m2m`: Create an M2M application
  - **Body**

    ```json
    {
      "name": "My automation",
      "scopes": "printer:read printer:write rtc:stream"
    }
    ```

  - **Response**: returns a one-time `client_secret` (store it; it won’t be returned again).

- `GET /api/admin/m2m`: List M2M applications (secrets are masked as `"********"`)
- `DELETE /api/admin/m2m/{client_id}`: Delete an M2M application

### System settings

- `GET /api/admin/settings`: Get system-wide settings
- `POST /api/admin/settings`: Update system-wide settings
  - Current settings include screenshot retention/count/cleanup interval:

    ```json
    {
      "screenshot_retention_hours": 24,
      "screenshot_max_count": 100,
      "screenshot_cleanup_interval_minutes": 60
    }
    ```

