# API Contracts

Last updated: 2026-05-27

This document defines the API contracts for the Spend Sense FastAPI backend. Auth endpoints are implemented; other sections remain planned work and should guide future Pydantic schemas, routers, frontend integration, and tests.

## Global Rules

- Base path: `/api/v1`
- Auth: `Authorization: Bearer <access_token>` for all endpoints except root, health, docs, register, login, and refresh.
- Content type: JSON unless the endpoint explicitly uses multipart upload or file download.
- Dates: `YYYY-MM-DD`
- Months: `YYYY-MM`
- Timestamps: ISO 8601 UTC strings.
- Money: JSON numbers with two decimal places accepted and returned.
- IDs: UUID strings.

## Error Shape

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [
      {
        "field": "amount",
        "message": "Amount must be greater than 0."
      }
    ]
  }
}
```

Common codes:

| HTTP | code |
| --- | --- |
| 400 | `bad_request` |
| 401 | `unauthorized` |
| 403 | `forbidden` |
| 404 | `not_found` |
| 409 | `conflict` |
| 422 | `validation_error` |
| 500 | `internal_error` |

## Health

### GET `/health`

Returns backend liveness.

Response:

```json
{
  "status": "ok"
}
```

## Auth

### POST `/auth/register`

Creates an account and returns tokens.

Request:

```json
{
  "email": "alex@example.com",
  "password": "StrongPass1!",
  "displayName": "Alex",
  "userType": "Professional"
}
```

Response `201`:

```json
{
  "user": {
    "id": "uuid",
    "email": "alex@example.com",
    "displayName": "Alex",
    "userType": "Professional",
    "onboardingCompleted": false,
    "isActive": true,
    "createdAt": "2026-05-27T00:00:00Z",
    "updatedAt": "2026-05-27T00:00:00Z"
  },
  "accessToken": "jwt",
  "refreshToken": "opaque-token",
  "tokenType": "bearer",
  "expiresIn": 900
}
```

### POST `/auth/login`

Request:

```json
{
  "email": "alex@example.com",
  "password": "StrongPass1!"
}
```

Response `200`: same token response as register.

### POST `/auth/refresh`

Request:

```json
{
  "refreshToken": "opaque-token"
}
```

Response `200`:

```json
{
  "accessToken": "jwt",
  "refreshToken": "opaque-token",
  "tokenType": "bearer",
  "expiresIn": 900
}
```

### POST `/auth/logout`

Revokes the current refresh token.

Request:

```json
{
  "refreshToken": "opaque-token"
}
```

Response `204`: empty body.

### GET `/auth/me`

Returns the authenticated user summary.

Response `200`:

```json
{
  "id": "uuid",
  "email": "alex@example.com",
  "displayName": "Alex",
  "userType": "Professional",
  "onboardingCompleted": false,
  "isActive": true,
  "createdAt": "2026-05-27T00:00:00Z",
  "updatedAt": "2026-05-27T00:00:00Z"
}
```

## Profile And Preferences

### GET `/me`

Returns user, preferences, notification preferences, and progress in one payload.

Response:

```json
{
  "user": {
    "id": "uuid",
    "email": "alex@example.com",
    "displayName": "Alex",
    "userType": "Professional",
    "onboardingCompleted": true
  },
  "preferences": {
    "currency": "INR",
    "defaultMonthlyIncome": 50000,
    "financialGoalsPreference": "Balanced",
    "preferredStartDay": 1,
    "monthlySavingTargetPercent": 20,
    "hourlyWage": 300,
    "activeMonth": "2026-05",
    "avatarUrl": "/avatars/girl.png"
  },
  "notifications": {
    "budgetLimit": true,
    "overspending": true,
    "goalReminders": true,
    "dailySpending": false,
    "weeklySummary": true,
    "achievements": true,
    "subscriptionRenewal": true,
    "timing": "Evening",
    "customTime": null
  },
  "progress": {
    "savingsStreak": 0,
    "xp": 0,
    "level": 1
  }
}
```

### PATCH `/me/profile`

Updates display name, user type, and onboarding status.

### PATCH `/me/preferences`

Updates profile preferences.

### PATCH `/me/notifications`

Updates alert preferences.

### POST `/me/onboarding`

Completes onboarding and optionally creates the current month budget.

Request:

```json
{
  "displayName": "Alex",
  "userType": "Family",
  "currency": "INR",
  "defaultMonthlyIncome": 50000,
  "monthlySavingTargetPercent": 20,
  "activeMonth": "2026-05"
}
```

## Categories

### GET `/categories`

Returns system categories plus user-owned categories. System categories are listed first.

Query params:

| name | type | notes |
| --- | --- | --- |
| `includeArchived` | boolean | defaults to `false` |

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "slug": "food",
      "name": "Food",
      "icon": "UtensilsCrossed",
      "color": "hsl(var(--cat-food))",
      "isSystem": true,
      "isArchived": false,
      "displayOrder": 0,
      "createdAt": "2026-05-28T00:00:00Z",
      "updatedAt": "2026-05-28T00:00:00Z"
    }
  ]
}
```

### POST `/categories`

Creates a custom category. `isSystem` is always `false` (server-set).

Request:

```json
{
  "slug": "coffee",
  "name": "Coffee",
  "icon": "Coffee",
  "color": "#6f4e37",
  "displayOrder": 10
}
```

Response `201`: same shape as item in list response.

Slug rules: lowercase alphanumeric, hyphens allowed, 1–50 chars, unique per user.

### PATCH `/categories/{categoryId}`

Updates a custom category. All fields optional. Returns `403` for system categories.

Request:

```json
{
  "name": "Morning Coffee",
  "color": "#8b6914"
}
```

Response `200`: updated category.

### DELETE `/categories/{categoryId}`

Soft-archives a custom category. System categories return `403`.
Categories with linked expenses return `409` unless `?force=true` is passed.

Query params:

| name | type | notes |
| --- | --- | --- |
| `force` | boolean | archive even if expenses exist; defaults to `false` |

Response `204`: empty body.

## Budgets

> **Implementation note**: Phase 3 uses UUID-based CRUD (`/budgets/{id}`) rather
> than the month-string path (`/budgets/{month}`) originally sketched. The month
> is supplied in the request body on create and returned as a `YYYY-MM` string in
> responses.

### GET `/budgets`

Returns a lightweight list of monthly budgets.

Query params:

| name | type | notes |
| --- | --- | --- |
| `from` | `YYYY-MM` | optional — start month, inclusive |
| `to` | `YYYY-MM` | optional — end month, inclusive |
| `categoryId` | UUID | optional — only budgets containing this allocation |
| `activeOnly` | boolean | when true, restricts to the current calendar month |

Response `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "month": "2026-05",
      "income": 50000,
      "warningThreshold": 0.80,
      "allocationCount": 5,
      "totalPlanned": 35000,
      "totalSpent": 12500,
      "isOverBudget": false,
      "createdAt": "2026-05-01T00:00:00Z",
      "updatedAt": "2026-05-01T00:00:00Z"
    }
  ],
  "totalReturned": 1
}
```

### POST `/budgets`

Creates a monthly budget. Returns `409` if a budget for that month already exists.

Request:

```json
{
  "month": "2026-05",
  "income": 50000,
  "warningThreshold": 0.80,
  "rollover": false,
  "categories": [
    {
      "categoryId": "uuid",
      "plannedAmount": 8000,
      "displayOrder": 0
    }
  ]
}
```

Field rules:
- `month`: required, `YYYY-MM`, must be a valid calendar month.
- `income`: optional, `>= 0`, defaults to `0`.
- `warningThreshold`: optional, fraction `0–1`, defaults to `0.80`.
- `rollover`: optional boolean. When `true`, copies allocations from the previous month as defaults; supplied `categories` override rolled-over allocations for the same category.
- `categories`: optional list. No duplicate `categoryId` values. Each `plannedAmount >= 0`.

Response `201`: same shape as `GET /budgets/{id}`.

### GET `/budgets/{budgetId}`

Returns a single budget with full per-category and month-level analytics.

Response `200`:

```json
{
  "id": "uuid",
  "month": "2026-05",
  "income": 50000,
  "warningThreshold": 0.80,
  "categories": [
    {
      "id": "uuid",
      "categoryId": "uuid",
      "category": {
        "id": "uuid",
        "slug": "food",
        "name": "Food",
        "icon": "UtensilsCrossed",
        "color": "hsl(var(--cat-food))",
        "isSystem": true,
        "isArchived": false,
        "displayOrder": 0,
        "createdAt": "2026-05-01T00:00:00Z",
        "updatedAt": "2026-05-01T00:00:00Z"
      },
      "plannedAmount": 8000,
      "displayOrder": 0,
      "analytics": {
        "spent": 3200,
        "remaining": 4800,
        "pctUsed": 40.00,
        "isOverBudget": false,
        "isNearLimit": false
      },
      "createdAt": "2026-05-01T00:00:00Z",
      "updatedAt": "2026-05-01T00:00:00Z"
    }
  ],
  "analytics": {
    "totalPlanned": 35000,
    "totalSpent": 12500,
    "totalRemaining": 22500,
    "pctUsed": 35.71,
    "projectedSpend": 22500,
    "isOverBudget": false
  },
  "createdAt": "2026-05-01T00:00:00Z",
  "updatedAt": "2026-05-01T00:00:00Z"
}
```

Analytics notes:
- `pctUsed`: `spent / planned * 100`; 0 when planned is 0 and nothing spent.
- `isNearLimit`: true when `pctUsed >= warningThreshold * 100` and not over budget.
- `projectedSpend`: `(totalSpent / daysElapsed) * daysInMonth`; 0 for future months.

### PATCH `/budgets/{budgetId}`

Partial update. At least one field required.

Request:

```json
{
  "income": 55000,
  "warningThreshold": 0.75
}
```

Response `200`: updated budget (same shape as GET response).

### DELETE `/budgets/{budgetId}`

Hard-deletes the budget and all its category allocations (CASCADE).
Expense records are not affected.

Response `204`: empty body.

## Expenses

### GET `/expenses`

Query params:

| name | type | notes |
| --- | --- | --- |
| `month` | `YYYY-MM` | shortcut — expands to full date range; cannot combine with dateFrom/dateTo |
| `dateFrom` | `YYYY-MM-DD` | optional |
| `dateTo` | `YYYY-MM-DD` | optional |
| `categoryId` | UUID | optional |
| `paymentMethod` | string | `cash`, `card`, `upi`, `bank_transfer`, `wallet`, `other` |
| `amountMin` | number | optional, > 0 |
| `amountMax` | number | optional, > 0 |
| `isRecurring` | boolean | optional |
| `tags` | string | comma-separated tag list; ALL must match (AND logic) |
| `q` | string | searches note and merchant fields |
| `sortBy` | string | `date` (default) or `amount` |
| `sortOrder` | string | `desc` (default) or `asc` |
| `limit` | integer | default `50`, max `200` |
| `cursor` | string | opaque cursor from previous response |

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "categoryId": "uuid",
      "category": {
        "id": "uuid",
        "slug": "food",
        "name": "Food",
        "icon": "UtensilsCrossed",
        "color": "hsl(var(--cat-food))",
        "isSystem": true,
        "isArchived": false,
        "displayOrder": 0,
        "createdAt": "2026-05-28T00:00:00Z",
        "updatedAt": "2026-05-28T00:00:00Z"
      },
      "amount": 250.75,
      "expenseDate": "2026-05-27",
      "note": "Lunch at Swiggy",
      "paymentMethod": "upi",
      "merchant": "Swiggy",
      "tags": ["food", "work"],
      "currency": "INR",
      "isRecurring": false,
      "paidByMemberId": null,
      "receiptFileId": null,
      "createdAt": "2026-05-27T00:00:00Z",
      "updatedAt": "2026-05-27T00:00:00Z"
    }
  ],
  "nextCursor": null,
  "totalReturned": 1
}
```

Pagination uses a cursor key of `(expense_date DESC, id DESC)` encoded as a base64 opaque string. Pass `nextCursor` from the previous response as `cursor` in the next request.

### POST `/expenses`

Request:

```json
{
  "categoryId": "uuid",
  "amount": 250.75,
  "expenseDate": "2026-05-27",
  "note": "Lunch at Swiggy",
  "paymentMethod": "upi",
  "merchant": "Swiggy",
  "tags": ["food", "work"],
  "currency": "INR",
  "isRecurring": false,
  "paidByMemberId": null,
  "receiptFileId": null
}
```

Field rules:
- `amount`: > 0, max 2 decimal places
- `expenseDate`: not more than 30 days in the future
- `tags`: max 10 items, each max 50 chars, lowercase
- `paymentMethod`: `cash | card | upi | bank_transfer | wallet | other`
- `currency`: `INR | USD | EUR`
- `receiptFileId`: reference to a previously uploaded file (placeholder for Phase 3)

Response `201`: same shape as expense item above.

### GET `/expenses/{expenseId}`

Returns one expense with embedded category.

Response `200`: same shape as expense item above.

### PATCH `/expenses/{expenseId}`

All fields optional. At least one field must be provided.

Updates category, amount, date, note, paymentMethod, merchant, tags, currency, isRecurring, paidByMemberId, or receiptFileId.

Response `200`: updated expense.

### DELETE `/expenses/{expenseId}`

Hard-deletes the expense and its split rows (CASCADE). Returns `404` if not found.

Response `204`: empty body.

## Receipt Uploads

### POST `/uploads/receipts`

Multipart upload field: `file`.

Response `201`:

```json
{
  "id": "uuid",
  "originalFilename": "receipt.jpg",
  "contentType": "image/jpeg",
  "sizeBytes": 123456,
  "url": "/api/v1/uploads/receipts/uuid"
}
```

### GET `/uploads/receipts/{fileId}`

Returns the receipt file if the authenticated user owns it.

## Savings Goals

### GET `/goals`

Query params:

| name | type | notes |
| --- | --- | --- |
| `status` | string | `active`, `completed`, `archived`; optional |

### POST `/goals`

Request:

```json
{
  "name": "Emergency Fund",
  "icon": "PiggyBank",
  "targetAmount": 100000,
  "currentAmount": 10000,
  "monthlyContribution": 5000,
  "targetDate": "2026-12-31",
  "color": "hsl(var(--primary))"
}
```

### GET `/goals/{goalId}`

Returns one goal with contribution history.

### PATCH `/goals/{goalId}`

Updates editable goal fields.

### DELETE `/goals/{goalId}`

Archives by default. A hard delete should require a dedicated admin-only path if ever needed.

### POST `/goals/{goalId}/contributions`

Request:

```json
{
  "amount": 5000,
  "contributedAt": "2026-05-27T00:00:00Z",
  "note": "May savings"
}
```

Response includes the updated goal.

## Analytics, Insights, And Reports

### GET `/analytics/monthly`

Query params:

| name | type |
| --- | --- |
| `month` | `YYYY-MM` |

Returns the same computed month stats currently produced by the local prediction engine: income, planned total, actual total, projected total, savings, savings rate, and per-category stats.

### GET `/insights`

Query params:

| name | type |
| --- | --- |
| `month` | `YYYY-MM` |

Returns computed warnings, tips, successes, and predictions. Insights are not persisted in phase 1.

### GET `/reports/monthly`

Query params:

| name | type |
| --- | --- |
| `month` | `YYYY-MM` |

Returns report data for the month.

### GET `/reports/monthly/export`

Query params:

| name | type | notes |
| --- | --- | --- |
| `month` | `YYYY-MM` | required |
| `format` | `csv` or `pdf` | required |

Returns a file download.

## Family & Shared Finance (Phase 7)

> **Implementation status**: Implemented in Phase 7.
> Role hierarchy: `Owner` > `Admin` > `Member`.
> Invitation tokens are 64-byte URL-safe random strings returned once; only their SHA-256 hash is stored.

### POST `/family`

Creates a new family group. The authenticated user becomes the **Owner**. Each user may own at most one family.

Request:

```json
{
  "name": "Dagwar Family",
  "currency": "INR"
}
```

Field rules:
- `name`: 1–100 chars, required, default `"Family Wallet"`.
- `currency`: `INR | USD | EUR`, default `INR`.

Response `201`:

```json
{
  "id": "uuid",
  "ownerUserId": "uuid",
  "name": "Dagwar Family",
  "currency": "INR",
  "members": [
    {
      "id": "uuid",
      "familyId": "uuid",
      "userId": "uuid",
      "name": "Megha",
      "role": "Owner",
      "email": "megha@example.com",
      "avatarUrl": null,
      "spendingLimit": null,
      "isActive": true,
      "createdAt": "2026-06-03T09:00:00Z",
      "updatedAt": "2026-06-03T09:00:00Z"
    }
  ],
  "createdAt": "2026-06-03T09:00:00Z",
  "updatedAt": "2026-06-03T09:00:00Z"
}
```

Returns `409` if the authenticated user already owns a family.

### GET `/family`

Returns all families the authenticated user belongs to (as any role).

Response `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "ownerUserId": "uuid",
      "name": "Dagwar Family",
      "currency": "INR",
      "memberCount": 3,
      "createdAt": "2026-06-03T09:00:00Z",
      "updatedAt": "2026-06-03T09:00:00Z"
    }
  ],
  "total": 1
}
```

### GET `/family/{familyId}`

Returns full family detail with embedded active member list.

Returns `403` if the caller is not an active member.
Returns `404` if the family does not exist.

Response `200`: same shape as POST `/family` response.

### PATCH `/family/{familyId}`

Update family name and/or currency. At least one field required.

Requires **Admin** or **Owner** role. Returns `403` for plain Members.

Request:

```json
{
  "name": "Dagwar Household",
  "currency": "USD"
}
```

Response `200`: updated family detail (same shape as GET response).

### DELETE `/family/{familyId}`

Hard-deletes the family and all cascaded data (members, invitations, settlements).

Requires **Owner** role. Returns `403` for Admin or Member callers.

Response `204`: empty body.

### POST `/family/{familyId}/invite`

Generate a single-use 72-hour invitation for an email address.

Requires **Admin** or **Owner** role.

Request:

```json
{
  "email": "sarah@example.com",
  "role": "Member"
}
```

Field rules:
- `role`: `Admin` or `Member`. `Owner` and `Child` are rejected with `422`.

Response `201`:

```json
{
  "invitationId": "uuid",
  "familyId": "uuid",
  "email": "sarah@example.com",
  "role": "Member",
  "invitationToken": "<raw-64-byte-urlsafe-token>",
  "expiresAt": "2026-06-06T09:00:00Z",
  "createdAt": "2026-06-03T09:00:00Z"
}
```

> **Security note**: `invitationToken` is returned exactly once. It is never stored on the server. Share it with the invitee via any out-of-band channel (messaging, email, etc.).

Returns `409` if:
- The email is already an active member.
- A pending non-expired invitation for the email already exists.
- The family has reached the maximum of 20 members.

### POST `/family/accept-invite`

Accept a family invitation using the raw token.

The authenticated user's email must match the invited email address.

Request:

```json
{
  "token": "<raw-64-byte-urlsafe-token>"
}
```

Response `201`: the new `FamilyMember` record (same shape as member in detail response).

Returns `400` if the token is invalid, expired, already accepted, or revoked.
Returns `409` if the caller is already an active member of the family.

### DELETE `/family/{familyId}/member/{memberId}`

Deactivate (soft-remove) a family member.

Permission matrix:
| Caller role | Can remove |
|---|---|
| Owner | Admin, Member |
| Admin | Member only |
| Member | — (403) |

- Returns `403` if the target is the family Owner.
- Returns `403` if an Admin tries to remove another Admin.
- Returns `403` if the caller tries to remove themselves (use `/leave`).
- Returns `404` if the member is not found in this family.

Response `204`: empty body.

### DELETE `/family/{familyId}/leave`

Voluntarily leave a family group. Deactivates the caller's member record.

- Returns `403` if the caller is the family Owner (delete the family instead).

Response `204`: empty body.

### GET `/family/{familyId}/analytics`

Returns aggregated expense, budget, and savings goal data across all active members.

Requires active membership (any role).

Response `200`:

```json
{
  "familyId": "uuid",
  "familyName": "Dagwar Family",
  "expenses": {
    "totalAmount": 45200.00,
    "expenseCount": 87,
    "topCategory": null,
    "currentMonthTotal": 12400.00
  },
  "budget": {
    "totalPlanned": 0,
    "totalSpent": 45200.00,
    "totalRemaining": 0,
    "memberCount": 3
  },
  "goals": {
    "totalGoals": 5,
    "activeGoals": 3,
    "completedGoals": 2,
    "totalSaved": 85000.00,
    "totalTarget": 200000.00
  },
  "generatedAt": "2026-06-03T09:00:00Z"
}
```



## Gamification

### GET `/progress`

Returns XP, level, streaks, and unlocked badge count.

### GET `/badges`

Returns badge catalog with unlocked state.

### GET `/challenges`

Query params:

| name | type | notes |
| --- | --- | --- |
| `date` | `YYYY-MM-DD` | optional |
| `status` | string | optional |

### POST `/challenges/generate`

Generates daily challenges for a date. Idempotent for the same user/date.

Request:

```json
{
  "date": "2026-05-27"
}
```

### PATCH `/challenges/{challengeId}`

Updates challenge status when the backend verifies completion.

### POST `/challenges/{challengeId}/claim`

Claims XP for a completed challenge.

## Local Store Import

### POST `/sync/import-local-store`

Imports the current Zustand persisted state for a newly authenticated user.

Request:

```json
{
  "storeVersion": "spend-sense-store-v1",
  "payload": {}
}
```

Response:

```json
{
  "imported": {
    "budgets": 1,
    "expenses": 12,
    "goals": 2,
    "familyMembers": 3,
    "badges": 0,
    "challenges": 3
  },
  "warnings": []
}
```

The import endpoint must be idempotent enough for retry. The implementation should either accept client-supplied legacy IDs in a mapping table or return a client-side remapping dictionary for newly created server IDs.
