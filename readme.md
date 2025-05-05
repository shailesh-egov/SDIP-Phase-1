# Provider enviornment file

# Setup Details and Environment Variables

## Provider System

### Environment Variables
- `DATABASE_URL`: MySQL database connection URL (e.g., `mysql+pymysql://admin:1234@mysql-db:3306/food_ration_db`)
- `RESULTS_DIR`: Directory to store results (default: `./results`)
- `ENCRYPTION_KEYS`: JSON object containing encryption keys (e.g., `{"v1": "base64-encoded-key"}`)
- `CURRENT_KEY_ID`: Current encryption key ID (e.g., `v1`)
- `CONTEXT_PATH`: API context path (default: `/provider`)
- `API_KEYS_ENABLED`: Enable API key validation (default: `True`)
- `DEFAULT_API_KEY`: Default API key (e.g., `secret123`)
- `DEFAULT_TENANT_ID`: Default tenant ID (e.g., `pension_system`)
- `DEFAULT_DEPARTMENT`: Default department name (e.g., `Old Pension`)

## Consumer System

### Environment Variables
- `DATABASE_URL`: MySQL database connection URL (e.g., `mysql://admin:1234@mysql-db:3306/pension_db`)
- `CONTEXT_PATH`: API context path (default: `/consumer`)
- `API_KEY`: API key for authentication (e.g., `secret123`)
- `PROVIDER_SERVICE_URL`: URL of the provider service (e.g., `http://provider-service:8000/provider`)
- `BATCH_SIZE`: Batch size for processing (default: `10000`)
- `SCHEDULER_TIME`: Scheduler time for batch processing (e.g., `01:00`)

### Notes
- Ensure that the `ENCRYPTION_KEYS` environment variable is a valid JSON object with base64-encoded keys.
- The `CURRENT_KEY_ID` must match one of the keys in `ENCRYPTION_KEYS`.
- Update the `DATABASE_URL` and other environment variables as per your deployment setup.
