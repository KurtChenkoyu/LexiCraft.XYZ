# Neo4j Setup Guide for LexiCraft MVP

This guide walks you through setting up Neo4j Aura Free for the Learning Point Cloud.

## Prerequisites

- Python 3.8 or higher
- Neo4j Aura Free account (or Docker for local development)

## Step 1: Set Up Neo4j Aura Free Instance

### Option A: Neo4j Aura Free (Recommended for MVP)

1. **Sign up for Neo4j Aura Free**
   - Go to https://neo4j.com/cloud/aura/
   - Click "Start Free" or "Try Free"
   - Create an account (or sign in with existing account)

2. **Create a Free Database**
   - After logging in, click "Create Database"
   - Select "Free" tier
   - Choose a database name (e.g., "lexicraft-learning-points")
   - Select a region (choose closest to your users)
   - Click "Create Database"

3. **Get Connection Details**
   - Once created, you'll see connection details:
     - **URI**: `neo4j+s://xxxxx.databases.neo4j.io`
     - **Username**: `neo4j` (default)
     - **Password**: Click "Show Password" to reveal (save this securely!)

4. **Test Connection in Browser**
   - Click "Open" to open Neo4j Browser
   - Try running: `RETURN 1 as test`
   - You should see `1` returned

### Option B: Docker (Local Development)

If you prefer local development:

```bash
docker run \
  --name neo4j-learning-points \
  -p7474:7474 -p7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -d \
  neo4j:latest
```

Then use:
- **URI**: `neo4j://localhost:7687`
- **Username**: `neo4j`
- **Password**: `password`

## Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Neo4j connection details:
   ```env
   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_actual_password_here
   ```

**Important**: Never commit `.env` to version control!

## Step 4: Initialize Schema

Run the schema initialization script to create constraints and indexes:

```bash
python -m src.database.neo4j_schema
```

You should see:
```
✓ Connection verified
Creating constraints...
Creating indexes...

Schema initialization results:
Constraints: {'learning_point_id': 'created or already exists', 'learning_point_word': 'created or already exists'}
Indexes: {'learning_point_tier': 'created or already exists', ...}
```

## Step 5: Test Connection

Run the connection test:

```bash
python tests/test_neo4j_connection.py
```

Expected output:
```
==================================================
Neo4j Connection and Schema Tests
==================================================
Testing Neo4j connection...
✓ Connection successful!

Testing schema initialization...
✓ Schema initialization successful!

==================================================
✓ All tests passed!
```

## Step 6: Test CRUD Operations

Test basic Create, Read, Update, Delete operations:

```bash
python tests/test_neo4j_crud.py
```

## Step 7: Test Relationship Queries

Test relationship creation and querying:

```bash
python tests/test_neo4j_relationships.py
```

## Project Structure

```
backend/
├── src/
│   ├── database/
│   │   ├── neo4j_connection.py      # Connection manager
│   │   ├── neo4j_schema.py           # Schema initialization
│   │   └── neo4j_crud/
│   │       ├── learning_points.py    # CRUD for nodes
│   │       └── relationships.py      # Relationship operations
│   └── models/
│       └── learning_point.py         # Pydantic models
├── tests/
│   ├── test_neo4j_connection.py     # Connection tests
│   ├── test_neo4j_crud.py           # CRUD tests
│   └── test_neo4j_relationships.py  # Relationship tests
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment template
└── README_NEO4J_SETUP.md            # This file
```

## Usage Examples

### Create a Learning Point

```python
from src.database.neo4j_connection import Neo4jConnection
from src.database.neo4j_crud.learning_points import create_learning_point
from src.models.learning_point import LearningPoint

conn = Neo4jConnection()

lp = LearningPoint(
    id="beat_around_the_bush",
    word="beat around the bush",
    type="idiom",
    tier=4,
    definition="To avoid talking about something directly",
    example="Stop beating around the bush and tell me what happened.",
    frequency_rank=1250,
    difficulty="B2",
    register="informal",
    contexts=["idiomatic", "conversational"],
    metadata={"pronunciation": "/biːt əˈraʊnd ðə bʊʃ/"}
)

create_learning_point(conn, lp)
conn.close()
```

### Create a Relationship

```python
from src.database.neo4j_crud.relationships import create_relationship
from src.models.learning_point import RelationshipType

create_relationship(
    conn,
    "beat",
    "beat_around_the_bush",
    RelationshipType.PREREQUISITE_OF
)
```

### Query Prerequisites

```python
from src.database.neo4j_crud.relationships import get_prerequisites

prereqs = get_prerequisites(conn, "beat_around_the_bush")
for prereq in prereqs:
    print(f"Prerequisite: {prereq['word']}")
```

## Relationship Types

The following relationship types are supported:

- `PREREQUISITE_OF`: A → B means you need A before B
- `COLLOCATES_WITH`: A ↔ B means A and B are often used together
- `RELATED_TO`: A ↔ B means A and B are similar/related
- `PART_OF`: A → B means A is part of B
- `OPPOSITE_OF`: A ↔ B means A and B are antonyms
- `MORPHOLOGICAL`: A → B with `{type: "prefix"|"suffix"}` for morphological relationships
- `REGISTER_VARIANT`: A → B means A is formal, B is informal (or vice versa)
- `FREQUENCY_RANK`: A → B means A is more common than B

## Troubleshooting

### Connection Issues

**Error**: `Connection verification failed`

**Solutions**:
1. Check that your `.env` file has correct credentials
2. Verify the URI format (should start with `neo4j+s://` for Aura)
3. Check that your IP is whitelisted (Aura may require IP whitelisting)
4. Verify the database is running (check Aura dashboard)

### Constraint Errors

**Error**: `Constraint already exists`

**Solution**: This is normal if you've run the schema initialization before. The script uses `IF NOT EXISTS` to handle this gracefully.

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Make sure you're running from the `backend/` directory, or add the backend directory to your Python path.

## Next Steps

After completing this setup:

1. ✅ Neo4j Aura instance created and connected
2. ✅ Schema initialized (constraints and indexes)
3. ✅ Connection tested
4. ✅ CRUD operations tested
5. ✅ Relationship queries tested

You're ready to:
- Populate the Learning Point Cloud with word data
- Integrate with the backend API
- Start building relationship discovery features

## Support

For issues or questions:
1. Check the handoff document: `docs/development/handoffs/HANDOFF_PHASE1_DATABASE_NEO4J.md`
2. Review Neo4j documentation: https://neo4j.com/docs/
3. Check deployment architecture: `docs/development/DEPLOYMENT_ARCHITECTURE.md`

