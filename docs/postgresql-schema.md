# PostgreSQL Schema

Last updated: 2026-05-27

This is the finalized PostgreSQL schema target for the first real persistence phase of the Spend Sense backend. It is a schema specification, not an applied migration yet. The first Alembic migration should implement this document unless the product scope changes first.

## Design Principles

- PostgreSQL is the system of record after backend persistence begins.
- Existing frontend concepts remain recognizable: monthly budgets, category plans, expenses, goals, family members, challenges, badges, and settings.
- Money is stored as `numeric(14,2)`.
- Primary keys are UUIDs generated in PostgreSQL.
- API month strings use `YYYY-MM`; database month columns use the first day of that month as `date`.
- Insights, analytics, and reports are computed from normalized records unless a later phase requires snapshots.

## Extensions

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

## Enums

```sql
CREATE TYPE currency_code AS ENUM ('INR', 'USD', 'EUR');
CREATE TYPE user_type AS ENUM ('Student', 'Family', 'Professional', 'Freelancer');
CREATE TYPE notification_timing AS ENUM ('Morning', 'Evening', 'Custom');
CREATE TYPE family_role AS ENUM ('Owner', 'Admin', 'Member', 'Child');
CREATE TYPE savings_goal_status AS ENUM ('active', 'completed', 'archived', 'paused');
CREATE TYPE badge_category AS ENUM ('streaks', 'savings', 'discipline', 'social');
CREATE TYPE challenge_type AS ENUM ('spending_limit', 'no_category', 'save_amount', 'zero_spend');
CREATE TYPE challenge_status AS ENUM ('active', 'completed', 'claimed', 'expired');
CREATE TYPE settlement_status AS ENUM ('pending', 'settled', 'cancelled');
```

## Tables

### users

Owns authentication identity and top-level account state.

```sql
CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text NOT NULL,
  password_hash text NOT NULL,
  display_name text NOT NULL,
  user_type user_type NOT NULL DEFAULT 'Professional',
  onboarding_completed boolean NOT NULL DEFAULT false,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT users_email_format_chk CHECK (position('@' in email) > 1)
);

CREATE UNIQUE INDEX users_email_lower_uidx ON users (lower(email));
```

### refresh_tokens

Stores hashed refresh tokens for session renewal and revocation.

```sql
CREATE TABLE refresh_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash text NOT NULL,
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  replaced_by_token_id uuid REFERENCES refresh_tokens(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_by_ip inet,
  user_agent text
);

CREATE UNIQUE INDEX refresh_tokens_token_hash_uidx ON refresh_tokens (token_hash);
CREATE INDEX refresh_tokens_user_id_idx ON refresh_tokens (user_id);
```

### user_preferences

Stores profile preferences that mirror the current frontend settings object.

```sql
CREATE TABLE user_preferences (
  user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  currency currency_code NOT NULL DEFAULT 'INR',
  default_monthly_income numeric(14,2) NOT NULL DEFAULT 0,
  financial_goals_preference text NOT NULL DEFAULT 'Balanced',
  preferred_start_day smallint NOT NULL DEFAULT 1,
  monthly_saving_target_percent numeric(5,2),
  hourly_wage numeric(14,2) NOT NULL DEFAULT 0,
  active_month date,
  avatar_url text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT user_preferences_income_chk CHECK (default_monthly_income >= 0),
  CONSTRAINT user_preferences_saving_target_chk CHECK (
    monthly_saving_target_percent IS NULL
    OR monthly_saving_target_percent BETWEEN 0 AND 100
  ),
  CONSTRAINT user_preferences_start_day_chk CHECK (preferred_start_day BETWEEN 1 AND 28),
  CONSTRAINT user_preferences_hourly_wage_chk CHECK (hourly_wage >= 0),
  CONSTRAINT user_preferences_active_month_chk CHECK (
    active_month IS NULL
    OR extract(day from active_month) = 1
  )
);
```

### notification_preferences

Stores alert preferences independently from profile preferences.

```sql
CREATE TABLE notification_preferences (
  user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  budget_limit boolean NOT NULL DEFAULT true,
  overspending boolean NOT NULL DEFAULT true,
  goal_reminders boolean NOT NULL DEFAULT true,
  daily_spending boolean NOT NULL DEFAULT false,
  weekly_summary boolean NOT NULL DEFAULT true,
  achievements boolean NOT NULL DEFAULT true,
  subscription_renewal boolean NOT NULL DEFAULT true,
  timing notification_timing NOT NULL DEFAULT 'Evening',
  custom_time time,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT notification_preferences_custom_time_chk CHECK (
    (timing = 'Custom' AND custom_time IS NOT NULL)
    OR (timing <> 'Custom' AND custom_time IS NULL)
  )
);
```

### user_progress

Stores gamification counters that are account-level rather than transaction-level.

```sql
CREATE TABLE user_progress (
  user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  savings_streak integer NOT NULL DEFAULT 0,
  xp integer NOT NULL DEFAULT 0,
  level integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT user_progress_savings_streak_chk CHECK (savings_streak >= 0),
  CONSTRAINT user_progress_xp_chk CHECK (xp >= 0),
  CONSTRAINT user_progress_level_chk CHECK (level >= 1)
);
```

### spending_categories

Stores system defaults and user-created custom categories.

```sql
CREATE TABLE spending_categories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  slug text NOT NULL,
  name text NOT NULL,
  icon text NOT NULL,
  color text NOT NULL,
  is_system boolean NOT NULL DEFAULT false,
  is_archived boolean NOT NULL DEFAULT false,
  display_order smallint NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT spending_categories_owner_chk CHECK (
    (is_system = true AND user_id IS NULL)
    OR (is_system = false AND user_id IS NOT NULL)
  ),
  CONSTRAINT spending_categories_slug_chk CHECK (length(trim(slug)) > 0),
  CONSTRAINT spending_categories_name_chk CHECK (length(trim(name)) > 0)
);

CREATE UNIQUE INDEX spending_categories_system_slug_uidx
  ON spending_categories (lower(slug))
  WHERE user_id IS NULL;

CREATE UNIQUE INDEX spending_categories_user_slug_uidx
  ON spending_categories (user_id, lower(slug))
  WHERE user_id IS NOT NULL;
```

Initial system category seed:

| slug | name | icon | color |
| --- | --- | --- | --- |
| `food` | Food | `UtensilsCrossed` | `hsl(var(--cat-food))` |
| `shopping` | Shopping | `ShoppingBag` | `hsl(var(--cat-shopping))` |
| `recharge` | Recharge | `Smartphone` | `hsl(var(--cat-recharge))` |
| `transport` | Transport | `Bus` | `hsl(var(--cat-transport))` |
| `rent` | Rent | `Home` | `hsl(var(--cat-rent))` |
| `medical` | Medical | `Stethoscope` | `hsl(var(--cat-medical))` |
| `electricity` | Electricity | `Zap` | `hsl(var(--cat-electricity))` |
| `others` | Others | `MoreHorizontal` | `hsl(var(--cat-others))` |

### monthly_budgets

Stores one budget per user per month.

```sql
CREATE TABLE monthly_budgets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  month date NOT NULL,
  income numeric(14,2) NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT monthly_budgets_month_chk CHECK (extract(day from month) = 1),
  CONSTRAINT monthly_budgets_income_chk CHECK (income >= 0),
  CONSTRAINT monthly_budgets_user_month_uidx UNIQUE (user_id, month)
);

CREATE INDEX monthly_budgets_user_month_idx ON monthly_budgets (user_id, month DESC);
```

### budget_category_allocations

Stores planned category allocations for a budget month.

```sql
CREATE TABLE budget_category_allocations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  budget_id uuid NOT NULL REFERENCES monthly_budgets(id) ON DELETE CASCADE,
  category_id uuid NOT NULL REFERENCES spending_categories(id) ON DELETE RESTRICT,
  planned_amount numeric(14,2) NOT NULL DEFAULT 0,
  display_order smallint NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT budget_category_allocations_amount_chk CHECK (planned_amount >= 0),
  CONSTRAINT budget_category_allocations_budget_category_uidx UNIQUE (budget_id, category_id)
);

CREATE INDEX budget_category_allocations_budget_idx ON budget_category_allocations (budget_id);
```

### families

Stores a user's family wallet container. Initial product scope supports one owned family wallet per user.

```sql
CREATE TABLE families (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name text NOT NULL DEFAULT 'Family Wallet',
  currency currency_code NOT NULL DEFAULT 'INR',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT families_name_chk CHECK (length(trim(name)) > 0)
);

CREATE UNIQUE INDEX families_owner_user_uidx ON families (owner_user_id);
```

### family_members

Stores family participants. A member may later link to a real user account through `user_id`.

```sql
CREATE TABLE family_members (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  family_id uuid NOT NULL REFERENCES families(id) ON DELETE CASCADE,
  user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  name text NOT NULL,
  role family_role NOT NULL DEFAULT 'Member',
  email text,
  avatar_url text,
  spending_limit numeric(14,2),
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT family_members_name_chk CHECK (length(trim(name)) > 0),
  CONSTRAINT family_members_spending_limit_chk CHECK (
    spending_limit IS NULL OR spending_limit >= 0
  )
);

CREATE INDEX family_members_family_idx ON family_members (family_id, is_active);

CREATE UNIQUE INDEX family_members_family_email_uidx
  ON family_members (family_id, lower(email))
  WHERE email IS NOT NULL;
```

### family_invitations

Stores pending invitations to join a family. The raw token is never persisted — only its SHA-256 hash.

```sql
CREATE TABLE family_invitations (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  family_id      uuid NOT NULL REFERENCES families(id) ON DELETE CASCADE,
  invited_by_id  uuid NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
  email          text NOT NULL,
  role           family_role NOT NULL DEFAULT 'Member',
  token_hash     text NOT NULL,
  expires_at     timestamptz NOT NULL,
  accepted_at    timestamptz,
  revoked_at     timestamptz,
  created_at     timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT family_invitations_email_chk CHECK (position('@' in email) > 1),
  CONSTRAINT family_invitations_terminal_state_chk CHECK (
    (accepted_at IS NULL) OR (revoked_at IS NULL)
  )
);

CREATE UNIQUE INDEX family_invitations_token_hash_uidx ON family_invitations (token_hash);
CREATE INDEX family_invitations_family_email_idx ON family_invitations (family_id, lower(email));
```

### uploaded_files

Stores receipt metadata. File bytes should live in local disk/object storage, not in this table.

```sql
CREATE TABLE uploaded_files (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  storage_provider text NOT NULL DEFAULT 'local',
  storage_key text NOT NULL,
  original_filename text,
  content_type text,
  size_bytes bigint,
  checksum_sha256 text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uploaded_files_size_chk CHECK (size_bytes IS NULL OR size_bytes >= 0)
);

CREATE UNIQUE INDEX uploaded_files_storage_key_uidx ON uploaded_files (storage_key);
CREATE INDEX uploaded_files_user_idx ON uploaded_files (user_id, created_at DESC);
```

### expenses

Stores individual expense records.

```sql
CREATE TABLE expenses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  category_id uuid NOT NULL REFERENCES spending_categories(id) ON DELETE RESTRICT,
  amount numeric(14,2) NOT NULL,
  expense_date date NOT NULL,
  note text NOT NULL DEFAULT '',
  paid_by_member_id uuid REFERENCES family_members(id) ON DELETE SET NULL,
  receipt_file_id uuid REFERENCES uploaded_files(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT expenses_amount_chk CHECK (amount > 0)
);

CREATE INDEX expenses_user_date_idx ON expenses (user_id, expense_date DESC, id DESC);
CREATE INDEX expenses_user_category_date_idx ON expenses (user_id, category_id, expense_date DESC);
CREATE INDEX expenses_paid_by_member_idx ON expenses (paid_by_member_id) WHERE paid_by_member_id IS NOT NULL;
```

### expense_splits

Stores split participants for family expenses.

```sql
CREATE TABLE expense_splits (
  expense_id uuid NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
  member_id uuid NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
  share_amount numeric(14,2) NOT NULL,
  is_settled boolean NOT NULL DEFAULT false,
  settled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (expense_id, member_id),
  CONSTRAINT expense_splits_share_amount_chk CHECK (share_amount >= 0),
  CONSTRAINT expense_splits_settled_at_chk CHECK (
    (is_settled = false AND settled_at IS NULL)
    OR (is_settled = true AND settled_at IS NOT NULL)
  )
);

CREATE INDEX expense_splits_member_idx ON expense_splits (member_id, is_settled);
```

### settlements

Stores explicit settlement transactions between family members.

```sql
CREATE TABLE settlements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  family_id uuid NOT NULL REFERENCES families(id) ON DELETE CASCADE,
  from_member_id uuid NOT NULL REFERENCES family_members(id) ON DELETE RESTRICT,
  to_member_id uuid NOT NULL REFERENCES family_members(id) ON DELETE RESTRICT,
  amount numeric(14,2) NOT NULL,
  currency currency_code NOT NULL DEFAULT 'INR',
  status settlement_status NOT NULL DEFAULT 'pending',
  note text,
  settled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT settlements_amount_chk CHECK (amount > 0),
  CONSTRAINT settlements_members_distinct_chk CHECK (from_member_id <> to_member_id),
  CONSTRAINT settlements_settled_at_chk CHECK (
    (status <> 'settled' AND settled_at IS NULL)
    OR (status = 'settled' AND settled_at IS NOT NULL)
  )
);

CREATE INDEX settlements_family_status_idx ON settlements (family_id, status, created_at DESC);
```

### savings_goals

Stores user savings targets.

```sql
CREATE TABLE savings_goals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name text NOT NULL,
  icon text NOT NULL,
  color text,
  description text,
  priority text,
  category text,
  target_amount numeric(14,2) NOT NULL,
  current_amount numeric(14,2) NOT NULL DEFAULT 0,
  monthly_contribution numeric(14,2) NOT NULL DEFAULT 0,
  target_date date,
  status savings_goal_status NOT NULL DEFAULT 'active',
  archived_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT savings_goals_name_chk CHECK (length(trim(name)) > 0),
  CONSTRAINT savings_goals_target_amount_chk CHECK (target_amount > 0),
  CONSTRAINT savings_goals_current_amount_chk CHECK (current_amount >= 0),
  CONSTRAINT savings_goals_monthly_contribution_chk CHECK (monthly_contribution >= 0),
  CONSTRAINT savings_goals_archived_at_chk CHECK (
    (status <> 'archived' AND archived_at IS NULL)
    OR (status = 'archived' AND archived_at IS NOT NULL)
  )
);

CREATE INDEX savings_goals_user_status_idx ON savings_goals (user_id, status, created_at DESC);
```

### goal_contributions

Stores contribution history for a savings goal.

```sql
CREATE TABLE goal_contributions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  goal_id uuid NOT NULL REFERENCES savings_goals(id) ON DELETE CASCADE,
  amount numeric(14,2) NOT NULL,
  contributed_at timestamptz NOT NULL DEFAULT now(),
  note text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT goal_contributions_amount_chk CHECK (amount > 0)
);

CREATE INDEX goal_contributions_goal_date_idx ON goal_contributions (goal_id, contributed_at DESC);
```

### badges

Stores the badge catalog.

```sql
CREATE TABLE badges (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code text NOT NULL,
  name text NOT NULL,
  icon text NOT NULL,
  description text NOT NULL,
  category badge_category NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT badges_code_chk CHECK (length(trim(code)) > 0),
  CONSTRAINT badges_name_chk CHECK (length(trim(name)) > 0)
);

CREATE UNIQUE INDEX badges_code_uidx ON badges (lower(code));
```

### user_badges

Stores unlocked badges for a user.

```sql
CREATE TABLE user_badges (
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  badge_id uuid NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
  unlocked_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, badge_id)
);

CREATE INDEX user_badges_user_unlocked_idx ON user_badges (user_id, unlocked_at DESC);
```

### challenges

Stores generated challenge instances.

```sql
CREATE TABLE challenges (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title text NOT NULL,
  description text NOT NULL,
  reward_xp integer NOT NULL,
  type challenge_type NOT NULL,
  target_value numeric(14,2),
  category_id uuid REFERENCES spending_categories(id) ON DELETE SET NULL,
  challenge_date date NOT NULL,
  status challenge_status NOT NULL DEFAULT 'active',
  completed_at timestamptz,
  claimed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT challenges_reward_xp_chk CHECK (reward_xp >= 0),
  CONSTRAINT challenges_target_value_chk CHECK (target_value IS NULL OR target_value >= 0),
  CONSTRAINT challenges_completed_at_chk CHECK (
    status NOT IN ('completed', 'claimed') OR completed_at IS NOT NULL
  ),
  CONSTRAINT challenges_claimed_at_chk CHECK (
    status <> 'claimed' OR claimed_at IS NOT NULL
  )
);

CREATE INDEX challenges_user_date_idx ON challenges (user_id, challenge_date DESC, status);
CREATE UNIQUE INDEX challenges_user_date_title_uidx ON challenges (user_id, challenge_date, lower(title));
```

## Local Storage Import Mapping

The import service should transform `spend-sense-store-v1` into the normalized schema:

| Frontend field | Destination |
| --- | --- |
| `settings.profile.userName` | `users.display_name` |
| `settings.userType` | `users.user_type` |
| `settings.onboardingCompleted` | `users.onboarding_completed` |
| `settings.profile.*` | `user_preferences` |
| `settings.notifications.*` | `notification_preferences` |
| `hourlyWage` | `user_preferences.hourly_wage` |
| `activeMonth` | `user_preferences.active_month` |
| `xp`, `level`, `savingsStreak` | `user_progress` |
| `budgets[month]` | `monthly_budgets` and `budget_category_allocations` |
| `expenses[]` | `expenses` and optional `expense_splits` |
| `goals[]` | `savings_goals` and `goal_contributions` |
| `familyMembers[]` | `families` and `family_members` |
| `badges[]` | `badges` and `user_badges` |
| `challenges[]` | `challenges` |

Default category ids such as `food` and `rent` should map to `spending_categories.slug`. Custom categories should be inserted as user-owned categories before importing budgets or expenses that reference them.

## Implementation Notes

- Add an `updated_at` trigger function in the first migration or update timestamps in application code consistently.
- SQLAlchemy models should mirror these table and constraint names to keep Alembic diffs readable.
- The first migration should create enums before tables and drop tables before enums on downgrade.
- Seed system categories and the initial badge catalog in the same migration or a dedicated seed step.
- Do not add persisted insight tables until there is a confirmed need to store dismissed insights, feedback, or generated report snapshots.
