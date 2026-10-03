# API

## `GET /`

Renders the profile form.

## `POST /generate-workout`

Accepts `username`, `user_id`, `age`, `weight`, `goal`, and `intensity` as form
fields. Returns the rendered result page. Invalid fields return HTTP 422;
database failures return HTTP 503.

## `GET /result/{plan_id}`

Renders the original or latest updated plan. Missing IDs return HTTP 404.

## `POST /submit-feedback`

Accepts `plan_id` and non-empty `feedback`. Saves the revised plan in
`updated_plan` and preserves the original. Missing plans return HTTP 404.

## `GET /view-all-users`

Renders stored users, user IDs, and original/updated plan data for the
coach/admin demonstration page.
