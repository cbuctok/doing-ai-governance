#!/usr/bin/env python3
"""
Standards Mapping Database Importer

This script:
1. Creates the database schema for standards mapping
2. Imports CSV files containing mappings between different standards
3. Provides utility functions for querying the mapping database

Usage:
  python3 standards_mapper.py setup         # Create database schema
  python3 standards_mapper.py import FILE   # Import a CSV file
  python3 standards_mapper.py import_dir DIRECTORY  # Import all CSVs in a directory
"""

import os
import sys
import csv
import logging
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import psycopg
from psycopg.rows import dict_row
from psycopg import sql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('standards_mapper.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection string
# Replace with your actual connection parameters
DB_CONNECTION_STRING = ""

# SQL for creating database schema
CREATE_SCHEMA_SQL = """
-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS import_logs CASCADE;
DROP TABLE IF EXISTS mappings CASCADE;
DROP TABLE IF EXISTS clauses CASCADE;
DROP TABLE IF EXISTS standards CASCADE;

-- Create the standards table
CREATE TABLE standards (
    standard_id SERIAL PRIMARY KEY,
    standard_name VARCHAR(255) NOT NULL UNIQUE
);

-- Create the clauses table
CREATE TABLE clauses (
    clause_id SERIAL PRIMARY KEY,
    standard_id INTEGER REFERENCES standards(standard_id) ON DELETE CASCADE,
    clause_text TEXT NOT NULL,
    UNIQUE(standard_id, clause_text)
);

-- Create the mappings table
CREATE TABLE mappings (
    mapping_id SERIAL PRIMARY KEY,
    clause_a_id INTEGER REFERENCES clauses(clause_id) ON DELETE CASCADE,
    clause_b_id INTEGER REFERENCES clauses(clause_id) ON DELETE CASCADE,
    source_file VARCHAR(255),
    UNIQUE(clause_a_id, clause_b_id)
);

-- Create import logs table
CREATE TABLE import_logs (
    import_id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Create indexes for performance
CREATE INDEX idx_clauses_standard_id ON clauses(standard_id);
CREATE INDEX idx_clauses_text ON clauses(clause_text varchar_pattern_ops);
CREATE INDEX idx_mappings_clause_a ON mappings(clause_a_id);
CREATE INDEX idx_mappings_clause_b ON mappings(clause_b_id);
"""

def get_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg.connect(DB_CONNECTION_STRING)
        return conn
    except psycopg.OperationalError as e:
        logger.error(f"Database connection error: {e}")
        sys.exit(1)

def setup_database():
    """Create the database schema."""
    logger.info("Setting up database schema...")
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_SCHEMA_SQL)
            conn.commit()
        logger.info("Database schema created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create database schema: {e}")
        return False

def normalize_text(text: str) -> str:
    """Normalize clause text to prevent duplicates due to formatting."""
    if not text:
        return ""
    # Replace multiple whitespace with single space
    normalized = ' '.join(text.split())
    return normalized.strip()

def extract_standard_name(header: str) -> str:
    """Extract the standard name from a column header."""
    # Common patterns in headers
    remove_suffixes = [" clauses", " requirements", " controls", " sections"]
    
    result = header.strip()
    for suffix in remove_suffixes:
        if result.lower().endswith(suffix.lower()):
            result = result[:-len(suffix)]
    
    return result.strip()

def get_or_create_standard(cur, standard_name: str) -> int:
    """Get or create a standard and return its ID."""
    if not standard_name:
        raise ValueError("Standard name cannot be empty")
    
    cur.execute(
        """
        INSERT INTO standards (standard_name) 
        VALUES (%s) 
        ON CONFLICT (standard_name) DO UPDATE 
        SET standard_name = EXCLUDED.standard_name 
        RETURNING standard_id
        """,
        (standard_name,)
    )
    return cur.fetchone()[0]

def get_or_create_clause(cur, standard_id: int, clause_text: str) -> Optional[int]:
    """Get or create a clause and return its ID."""
    if not clause_text:
        return None
    
    normalized_text = normalize_text(clause_text)
    if not normalized_text:
        return None
        
    cur.execute(
        """
        INSERT INTO clauses (standard_id, clause_text) 
        VALUES (%s, %s) 
        ON CONFLICT (standard_id, clause_text) DO UPDATE 
        SET clause_text = EXCLUDED.clause_text 
        RETURNING clause_id
        """,
        (standard_id, normalized_text)
    )
    return cur.fetchone()[0]

def create_mapping(cur, clause_a_id: int, clause_b_id: int, source_file: str) -> Optional[int]:
    """Create a mapping between two clauses if both exist."""
    if not clause_a_id or not clause_b_id:
        return None
        
    try:
        cur.execute(
            """
            INSERT INTO mappings (clause_a_id, clause_b_id, source_file) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (clause_a_id, clause_b_id) DO NOTHING
            RETURNING mapping_id
            """,
            (clause_a_id, clause_b_id, source_file)
        )
        result = cur.fetchone()
        return result[0] if result else None
    except Exception as e:
        logger.warning(f"Failed to create mapping: {e}")
        return None

def log_import(cur, file_name: str, row_count: int = 0, success: bool = True, error_message: str = None) -> int:
    """Log an import operation."""
    cur.execute(
        """
        INSERT INTO import_logs (file_name, row_count, success, error_message) 
        VALUES (%s, %s, %s, %s)
        RETURNING import_id
        """,
        (file_name, row_count, success, error_message)
    )
    return cur.fetchone()[0]

def update_import_log(cur, import_id: int, row_count: int, success: bool = True, error_message: str = None):
    """Update an existing import log."""
    cur.execute(
        """
        UPDATE import_logs 
        SET row_count = %s, success = %s, error_message = %s
        WHERE import_id = %s
        """,
        (row_count, success, error_message, import_id)
    )

def import_csv_file(file_path: str) -> bool:
    """Import a CSV file containing standard mappings."""
    file_path = Path(file_path)
    if not file_path.exists() or not file_path.is_file():
        logger.error(f"File not found: {file_path}")
        return False
        
    logger.info(f"Importing file: {file_path}")
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Log the start of import
                import_id = log_import(cur, str(file_path))
                
                # Open and process the CSV
                with open(file_path, 'r', encoding='utf-8') as csvfile:
                    # Try to detect dialect
                    sample = csvfile.read(4096)
                    csvfile.seek(0)
                    
                    try:
                        dialect = csv.Sniffer().sniff(sample)
                        reader = csv.reader(csvfile, dialect)
                    except csv.Error:
                        # Fall back to default dialect
                        reader = csv.reader(csvfile)
                    
                    # Process header row
                    try:
                        headers = next(reader)
                    except StopIteration:
                        update_import_log(cur, import_id, 0, False, "Empty CSV file")
                        conn.commit()
                        return False
                    
                    if len(headers) < 2:
                        update_import_log(cur, import_id, 0, False, 
                                        f"Invalid CSV format. Expected at least 2 columns, got {len(headers)}")
                        conn.commit()
                        return False
                    
                    # Extract standard names from headers
                    std_a_name = extract_standard_name(headers[0])
                    std_b_name = extract_standard_name(headers[1])
                    
                    logger.info(f"Mapping standards: '{std_a_name}' to '{std_b_name}'")
                    
                    # Get or create standard IDs
                    std_a_id = get_or_create_standard(cur, std_a_name)
                    std_b_id = get_or_create_standard(cur, std_b_name)
                    
                    # Process rows
                    row_count = 0
                    mapping_count = 0
                    
                    for row_num, row in enumerate(reader, start=2):  # Start from 2 to account for header row
                        if len(row) < 2:
                            logger.warning(f"Skipping row {row_num} - insufficient columns")
                            continue
                            
                        row_count += 1
                        
                        # Process clauses for standard A
                        clause_a_text = row[0].strip()
                        clause_a_id = get_or_create_clause(cur, std_a_id, clause_a_text) if clause_a_text else None
                        
                        # Process clauses for standard B
                        clause_b_text = row[1].strip()
                        clause_b_id = get_or_create_clause(cur, std_b_id, clause_b_text) if clause_b_text else None
                        
                        # Create mapping if both clauses exist
                        if clause_a_id and clause_b_id:
                            mapping_id = create_mapping(cur, clause_a_id, clause_b_id, str(file_path))
                            if mapping_id:
                                mapping_count += 1
                    
                    # Update import log
                    update_import_log(cur, import_id, row_count)
                    logger.info(f"Imported {row_count} rows, created {mapping_count} mappings")
                
                conn.commit()
                return True
                
    except Exception as e:
        logger.error(f"Error importing file {file_path}: {e}")
        # Try to update the import log if possible
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    update_import_log(cur, import_id, 0, False, str(e))
                conn.commit()
        except:
            pass
        return False

def import_directory(directory_path: str) -> Tuple[int, int]:
    """Import all CSV files in a directory."""
    directory_path = Path(directory_path)
    if not directory_path.exists() or not directory_path.is_dir():
        logger.error(f"Directory not found: {directory_path}")
        return (0, 0)
    
    logger.info(f"Importing all CSV files from: {directory_path}")
    
    csv_files = list(directory_path.glob("*.csv"))
    if not csv_files:
        logger.warning(f"No CSV files found in {directory_path}")
        return (0, 0)
    
    success_count = 0
    total_count = len(csv_files)
    
    for csv_file in csv_files:
        if import_csv_file(csv_file):
            success_count += 1
    
    logger.info(f"Imported {success_count} of {total_count} CSV files successfully")
    return (success_count, total_count)

def query_mapping_statistics() -> Dict[str, Any]:
    """Query and return statistics about the database."""
    try:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Get standard counts
                cur.execute("SELECT COUNT(*) as standard_count FROM standards")
                result = cur.fetchone()
                standard_count = result['standard_count']
                
                # Get clause counts
                cur.execute("SELECT COUNT(*) as clause_count FROM clauses")
                result = cur.fetchone()
                clause_count = result['clause_count']
                
                # Get mapping counts
                cur.execute("SELECT COUNT(*) as mapping_count FROM mappings")
                result = cur.fetchone()
                mapping_count = result['mapping_count']
                
                # Get standard-specific stats
                cur.execute("""
                    SELECT s.standard_name, COUNT(c.clause_id) as clause_count
                    FROM standards s
                    LEFT JOIN clauses c ON s.standard_id = c.standard_id
                    GROUP BY s.standard_name
                    ORDER BY s.standard_name
                """)
                standard_stats = cur.fetchall()
                
                # Get mapping pair stats
                cur.execute("""
                    SELECT 
                        sa.standard_name as standard_a,
                        sb.standard_name as standard_b,
                        COUNT(m.mapping_id) as mapping_count
                    FROM mappings m
                    JOIN clauses ca ON m.clause_a_id = ca.clause_id
                    JOIN clauses cb ON m.clause_b_id = cb.clause_id
                    JOIN standards sa ON ca.standard_id = sa.standard_id
                    JOIN standards sb ON cb.standard_id = sb.standard_id
                    GROUP BY sa.standard_name, sb.standard_name
                    ORDER BY sa.standard_name, sb.standard_name
                """)
                mapping_stats = cur.fetchall()
                
                return {
                    "standard_count": standard_count,
                    "clause_count": clause_count,
                    "mapping_count": mapping_count,
                    "standard_stats": standard_stats,
                    "mapping_stats": mapping_stats
                }
    except Exception as e:
        logger.error(f"Error querying database statistics: {e}")
        return {}

def print_statistics(stats: Dict[str, Any]):
    """Print database statistics."""
    if not stats:
        print("No statistics available.")
        return
        
    print("\n=== Standards Mapping Database Statistics ===")
    print(f"Total Standards: {stats['standard_count']}")
    print(f"Total Clauses: {stats['clause_count']}")
    print(f"Total Mappings: {stats['mapping_count']}")
    
    print("\n--- Standards and Clause Counts ---")
    for std in stats.get('standard_stats', []):
        print(f"  {std['standard_name']}: {std['clause_count']} clauses")
    
    print("\n--- Mapping Pairs ---")
    for mapping in stats.get('mapping_stats', []):
        print(f"  {mapping['standard_a']} → {mapping['standard_b']}: {mapping['mapping_count']} mappings")
    
    print("\n=======================================")

def main():
    parser = argparse.ArgumentParser(description="Standards Mapping Database Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up the database schema")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import a CSV file")
    import_parser.add_argument("file", help="Path to CSV file to import")
    
    # Import directory command
    import_dir_parser = subparsers.add_parser("import_dir", help="Import all CSV files in a directory")
    import_dir_parser.add_argument("directory", help="Path to directory containing CSV files")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        setup_database()
    
    elif args.command == "import":
        import_csv_file(args.file)
    
    elif args.command == "import_dir":
        import_directory(args.directory)
    
    elif args.command == "stats":
        stats = query_mapping_statistics()
        print_statistics(stats)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()