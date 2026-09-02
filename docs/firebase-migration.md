# RAVEN Firebase Data Migration Guide

## Migration Utility Usage
The data migration utility `scripts/migrate_to_firebase.py` reads existing relational tables (SQLite/PostgreSQL) and writes documents to Firestore collections.

### Dry-Run Validation Mode
To inspect and validate the migration count without modifying Firestore:
```bash
python scripts/migrate_to_firebase.py --dry-run
```

### Live Data Migration
To execute the live data migration:
```bash
python scripts/migrate_to_firebase.py --db-url "sqlite:///./raven_local.db"
```
