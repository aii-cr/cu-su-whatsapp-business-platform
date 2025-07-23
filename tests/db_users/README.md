# db_users Utility Scripts

This directory contains utility scripts for managing users, roles, and permissions in your MongoDB database for development and testing purposes.

## Scripts Overview

### 1. `insert_test_user.py`
- **Purpose:** Inserts a superadmin test user (`testuser@example.com`) with no roles but with `is_super_admin=True`.
- **Usage:**
  ```bash
  python -m tests.db_users.insert_test_user
  ```

### 2. `insert_normal_test_user.py`
- **Purpose:** Inserts a normal (non-superadmin) test user (`pytestuser@example.com`) with a role and at least one permission (`users:read`).
- **Usage:**
  ```bash
  python -m tests.db_users.insert_normal_test_user
  ```

### 3. `role_permission_manager.py`
- **Purpose:** Manage roles and permissions. Add new roles, append permissions to roles, and delete roles or permissions. Handles duplicates gracefully.
- **Commands:**
  - **Add a new role (with permissions):**
    ```bash
    python -m tests.db_users.role_permission_manager add-role "RoleName" --permissions users:read messages:send
    ```
  - **Append permissions to an existing role:**
    ```bash
    python -m tests.db_users.role_permission_manager append-perms "RoleName" users:read messages:send
    ```
  - **Delete a role:**
    ```bash
    python -m tests.db_users.role_permission_manager delete-role "RoleName"
    ```
  - **Delete a permission:**
    ```bash
    python -m tests.db_users.role_permission_manager delete-perm "users:read"
    ```

### 4. `user_role_manager.py`
- **Purpose:** Assign an existing role to a user by email. If the user already has the role, prints a warning.
- **Usage:**
  ```bash
  python -m tests.db_users.user_role_manager user@example.com "RoleName"
  ```

---

## Notes
- All scripts must be run from the project root (e.g., `/home/sa/dev/cu-su-backend`).
- All scripts use the FastAPI/MongoDB connection logic from your app, so your environment variables and DB must be configured.
- These scripts are for development and testing. Do **not** use them in production environments.

---

## Example Workflow

1. **Add a new permission and role:**
   ```bash
   python -m tests.db_users.role_permission_manager add-role "SupportAgent" --permissions messages:send users:read
   ```
2. **Append a permission to an existing role:**
   ```bash
   python -m tests.db_users.role_permission_manager append-perms "SupportAgent" messages:read
   ```
3. **Assign a role to a user:**
   ```bash
   python -m tests.db_users.user_role_manager pytestuser@example.com "SupportAgent"
   ```
4. **Delete a role or permission:**
   ```bash
   python -m tests.db_users.role_permission_manager delete-role "SupportAgent"
   python -m tests.db_users.role_permission_manager delete-perm "messages:read"
   ```

---

For any questions or improvements, update the scripts or this README as needed! 