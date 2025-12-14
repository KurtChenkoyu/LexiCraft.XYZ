# Multiprocessing Issue Analysis

## Problem
MCQ generation works fine with single worker but hangs/fails with multiple workers (multiprocessing).

## Key Code Sections

### 1. Multiprocessing Pool Setup
```python
# backend/scripts/generate_all_mcqs.py lines 378-380
from multiprocessing import Pool

with Pool(processes=num_workers) as pool:
    results = pool.starmap(process_sense_batch, worker_args)
```

### 2. Worker Function - Database Connection
```python
# backend/scripts/generate_all_mcqs.py lines 119-132
def process_sense_batch(sense_ids, worker_id, skip_existing, mcq_type_filter):
    # Each worker creates its own connection
    import importlib.util
    from pathlib import Path
    
    postgres_path = Path(__file__).parent.parent / "src" / "database" / "postgres_connection.py"
    spec = importlib.util.spec_from_file_location("postgres_connection", postgres_path)
    postgres_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(postgres_module)
    PostgresConnection = postgres_module.PostgresConnection
    
    pg_conn = PostgresConnection()
    db_session = pg_conn.get_session()
```

### 3. Global Engine Singleton Issue
```python
# backend/src/database/postgres_connection.py lines 17-53
# Global engine singleton - reuse across requests
_engine = None
_SessionLocal = None

def _get_engine():
    global _engine, _SessionLocal
    
    if _engine is None:
        _engine = create_engine(
            connection_string,
            poolclass=NullPool,  # Essential for Transaction mode
            connect_args={
                "sslmode": "require",
                "connect_timeout": 30,
            },
            echo=False
        )
        _SessionLocal = sessionmaker(...)
    
    return _engine, _SessionLocal
```

### 4. PostgresConnection Class
```python
# backend/src/database/postgres_connection.py lines 78-119
class PostgresConnection:
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        
        # Use global engine if using default connection string
        if self.connection_string == os.getenv("DATABASE_URL"):
            self.engine, self.SessionLocal = _get_engine()  # <-- Uses global singleton
        else:
            # Custom connection string - create new engine
            self.engine = create_engine(...)
```

## Suspected Issues

1. **Global Engine Singleton in Multiprocessing**: The `_engine` and `_SessionLocal` are global variables. In multiprocessing, each worker process gets its own copy of globals, but SQLAlchemy engines may not be fork-safe.

2. **SSL Connection Sharing**: Supabase uses SSL connections. When processes fork, SSL connections may not be properly inherited, causing hangs.

3. **Session State**: Each worker creates a session, but if the underlying engine connection is shared or not properly isolated, sessions may conflict.

4. **NullPool with Multiprocessing**: Using `NullPool` means no connection pooling, but in multiprocessing, each process needs its own isolated connection.

## What Works
- Single worker: ✅ Works (slow but reliable)
- Direct function calls: ✅ Works
- Database writes: ✅ Works (with retry logic)

## What Fails
- Multiple workers (Pool): ❌ Hangs after starting workers
- No error messages: Process just stops responding

## Questions for Gemini
1. Is SQLAlchemy engine fork-safe? Should we create engines per process?
2. How to properly isolate database connections in multiprocessing with Supabase SSL?
3. Should we use `multiprocessing.get_context('spawn')` instead of 'fork'?
4. Is the global singleton pattern causing issues when processes fork?
5. Should each worker create its own engine instead of sharing the global one?

---

## ✅ SOLUTION IMPLEMENTED (December 2025)

### Root Cause
SQLAlchemy engines are **not fork-safe**. When using default `fork` multiprocessing:
- Child processes inherit the parent's engine and connection pool
- SSL connections cannot be shared across processes
- Mutex locks on connections cause deadlocks

### Fix Applied
**Switched to `spawn` context** in `backend/scripts/generate_all_mcqs.py`:

```python
# Changed from:
from multiprocessing import Pool
with Pool(processes=num_workers) as pool:

# To:
import multiprocessing
ctx = multiprocessing.get_context('spawn')
with ctx.Pool(processes=num_workers) as pool:
```

### Why `spawn` Works
- Creates **fresh Python processes** (not forks)
- Each worker starts with clean state
- No inherited SSL connections or mutex locks
- Each process creates its own database connections

### Status
✅ **FIXED** - Multiprocessing now works correctly with PostgreSQL SSL connections

