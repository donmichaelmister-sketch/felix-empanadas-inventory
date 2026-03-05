#!/usr/bin/env python3
"""
SQLite database for inventory management.
Creates tables, handles reads/writes.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_FILE = Path(__file__).parent / "inventory.db"

def init_db():
    """Create database tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Bags table
    c.execute('''CREATE TABLE IF NOT EXISTS bags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bag_num INTEGER UNIQUE NOT NULL,
        flavor TEXT NOT NULL,
        date_made TEXT NOT NULL,
        count INTEGER NOT NULL,
        location TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Transfers table
    c.execute('''CREATE TABLE IF NOT EXISTS transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        from_location TEXT NOT NULL,
        to_location TEXT NOT NULL,
        bags TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Sales table
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        location TEXT NOT NULL,
        flavor TEXT NOT NULL,
        qty_sold INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_FILE}")

def add_bag(bag_num, flavor, count, location):
    """Add a new bag."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    date = datetime.now().strftime("%m/%d/%Y")
    
    try:
        c.execute('''INSERT INTO bags (bag_num, flavor, date_made, count, location)
                     VALUES (?, ?, ?, ?, ?)''',
                  (bag_num, flavor, date, count, location))
        conn.commit()
        print(f"✅ Added Bag #{bag_num} - {flavor} ({count})")
        return True
    except sqlite3.IntegrityError:
        print(f"❌ Bag #{bag_num} already exists")
        return False
    finally:
        conn.close()

def log_transfer(from_loc, to_loc, bags):
    """Log a transfer."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    date = datetime.now().strftime("%m/%d/%Y")
    bags_str = ", ".join(str(b) for b in bags)
    
    c.execute('''INSERT INTO transfers (date, from_location, to_location, bags)
                 VALUES (?, ?, ?, ?)''',
              (date, from_loc, to_loc, bags_str))
    conn.commit()
    conn.close()
    print(f"✅ Transfer logged: {from_loc} → {to_loc}")

def get_bags():
    """Get all bags."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT bag_num, flavor, date_made, count, location FROM bags ORDER BY bag_num')
    rows = c.fetchall()
    conn.close()
    return rows

def get_bag_by_num(bag_num):
    """Get a specific bag."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM bags WHERE bag_num = ?', (bag_num,))
    row = c.fetchone()
    conn.close()
    return row

def update_bag_location(bag_num, new_location):
    """Update a bag's location."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE bags SET location = ? WHERE bag_num = ?',
              (new_location, bag_num))
    conn.commit()
    conn.close()

def get_inventory_summary():
    """Get current inventory by location."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    summary = {}
    c.execute('SELECT location, flavor, COUNT(*), SUM(count) FROM bags GROUP BY location, flavor')
    for location, flavor, bag_count, total_count in c.fetchall():
        if location not in summary:
            summary[location] = {}
        summary[location][flavor] = {'bags': bag_count, 'count': total_count}
    
    conn.close()
    return summary

if __name__ == "__main__":
    init_db()
    print("\n✅ Database ready for use")
