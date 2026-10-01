# FitBuddy REST API & Endpoint Reference

FitBuddy provides both interactive HTML user interfaces rendered via Jinja2 and RESTful endpoints for integration and automated testing.

Interactive OpenAPI documentation is automatically served at:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **OpenAPI Schema**: `http://127.0.0.1:8000/openapi.json`

---

## 1. Plan Generation & User Flow

### `GET /`
- **Description**: Renders the homepage intake form (`index.html`).
- **Response**: `200 OK` (text/html).

---

### `POST /generate-workout`
- **Description**: Accepts user profile data via HTML form, queries Gemini 1.5 Pro for a 7-day workout routine and Gemini Flash for a nutrition tip, persists both to SQLite, and returns the rendered plan page (`result.html`).
- **Content-Type**: `application/x-www-form-urlencoded`
- **Request Parameters (`UserInput` Schema)**:
  | Parameter | Type | Required | Constraints / Description |
  | --- | --- | --- | --- |
  | `username` | string | Yes | 1 to 100 characters. User display name. |
  | `user_id` | string | Yes | 1 to 50 characters. Unique business identifier (e.g. `alex_01`). |
  | `age` | integer | Yes | 10 to 100 years. |
  | `weight` | float | Yes | $\ge 20.0$ kg. |
  | `goal` | string | Yes | One of: `Weight Loss`, `Muscle Gain`, `Improve Endurance`, `General Fitness`, `Flexibility & Mobility`. |
  | `intensity` | string | Yes | One of: `low`, `medium`, `high`. |
  | `experience_level` | string | Yes | One of: `Beginner`, `Intermediate`, `Advanced`. |
- **Responses**:
  - `200 OK`: Returns rendered `result.html` with plan, progress tracker, and nutrition tip.
  - `422 Unprocessable Entity`: Validation failure on missing, out-of-bounds, or invalid fields.
  - `503 Service Unavailable`: Database persistence error.

---

### `GET /result/{plan_id}`
- **Description**: Displays the active workout plan (original or updated version) and nutrition advice for a specific `plan_id`.
- **Path Parameters**:
  - `plan_id` (integer, required): Database primary key of the plan.
- **Responses**:
  - `200 OK`: Returns rendered `result.html`.
  - `404 Not Found`: Plan ID does not exist in the database.

---

### `POST /submit-feedback`
- **Description**: Submits natural-language refinement feedback on an existing plan. Gemini 1.5 Pro modifies the schedule according to user instructions and saves the result to `updated_plan` without altering `original_plan`.
- **Content-Type**: `application/x-www-form-urlencoded`
- **Request Parameters (`FeedbackRequest` Schema)**:
  | Parameter | Type | Required | Description |
  | --- | --- | --- | --- |
  | `plan_id` | integer | Yes | ID of the plan to modify ($> 0$). |
  | `feedback` | string | Yes | Natural-language instructions (e.g., *"add yoga on day 4"*, *"reduce knee strain"*). |
- **Responses**:
  - `200 OK`: Returns updated `result.html` with "Plan Updated" indicator.
  - `404 Not Found`: Plan ID does not exist.
  - `422 Unprocessable Entity`: Missing or empty feedback.

---

## 2. Progress Tracking Endpoints

### `GET /progress/{user_id}`
- **Description**: Fetches real-time workout completion summary for a user.
- **Path Parameters**:
  - `user_id` (integer or string): Primary key or custom user ID.
- **Responses**:
  - `200 OK` (JSON):
    ```json
    {
      "user_id": 1,
      "completed_days": 2,
      "total_days": 7,
      "progress_percentage": 28,
      "day_status": {
        "1": true,
        "2": true,
        "3": false,
        "4": false,
        "5": false,
        "6": false,
        "7": false
      },
      "last_activity": "2026-10-30T17:00:00Z"
    }
    ```
  - `404 Not Found`: User not found.

---

### `POST /progress/{user_id}/{day_number}/complete`
- **Description**: Marks a specific workout day (1 through 7) as completed. Idempotent: repeated completions are safely ignored.
- **Path Parameters**:
  - `user_id` (integer or string): User identifier.
  - `day_number` (integer): Day index between 1 and 7.
- **Responses**:
  - `303 See Other`: Redirects back to `/result/{plan_id}`.
  - `400 Bad Request`: `day_number` out of 1–7 range.
  - `404 Not Found`: User does not exist.

---

## 3. Coach & Admin Management Endpoints

### `GET /view-all-users`
- **Description**: Displays the administrative dashboard (`all_users.html`) detailing all registered users, fitness metrics, progress indicators, and plan data.
- **Responses**:
  - `200 OK`: Returns rendered admin dashboard.

---

### `POST /admin/users/{user_id}/delete`
- **Description**: Deletes a user account and cascades deletion across all associated plans and workout progress records.
- **Path Parameters**:
  - `user_id` (integer): Database primary key of the user.
- **Responses**:
  - `303 See Other`: Redirects to `/view-all-users`.
  - `404 Not Found`: User not found.
