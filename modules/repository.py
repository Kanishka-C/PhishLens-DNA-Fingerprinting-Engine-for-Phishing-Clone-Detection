import sqlite3
import json
import os
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'dna_repository.db')

def init_db():
    """Initializes the SQLite database with the required schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trusted_sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            tag_sequence TEXT NOT NULL,
            metadata TEXT NOT NULL,
            structure_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_trusted_site(domain: str, dna: Dict[str, Any]):
    """Adds or updates a legitimate website's DNA in the repository."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO trusted_sites (domain, tag_sequence, metadata, structure_hash)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(domain) DO UPDATE SET 
            tag_sequence=excluded.tag_sequence,
            metadata=excluded.metadata,
            structure_hash=excluded.structure_hash
    ''', (domain, dna['tag_sequence'], json.dumps(dna['metadata']), dna['structure_hash']))
    conn.commit()
    conn.close()

def get_all_trusted_sites() -> List[Dict[str, Any]]:
    """Retrieves all trusted sites from the repository."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT domain, tag_sequence, metadata, structure_hash FROM trusted_sites')
    rows = cursor.fetchall()
    conn.close()
    
    sites = []
    for row in rows:
        sites.append({
            'domain': row[0],
            'dna': {
                'tag_sequence': row[1],
                'metadata': json.loads(row[2]),
                'structure_hash': row[3]
            }
        })
    return sites

# Ensure DB is initialized when module loads
init_db()
