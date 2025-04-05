from sqlalchemy import create_engine, text

def migrate():
    # Use synchronous SQLite URL
    engine = create_engine("sqlite:///uploads.db")
    
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='uploads';
        """))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            # Create table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE uploads (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    processed_filename TEXT,
                    filled_filename TEXT,
                    error_message TEXT,
                    color_count INTEGER NOT NULL DEFAULT 20,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
        else:
            # Add color_count column if it doesn't exist
            try:
                conn.execute(text("""
                    ALTER TABLE uploads 
                    ADD COLUMN color_count INTEGER NOT NULL DEFAULT 20;
                """))
            except Exception as e:
                print("Column might already exist:", e)
        
        # Add check constraint (will fail silently if it already exists)
        try:
            conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS check_color_count
                BEFORE INSERT ON uploads
                BEGIN
                    SELECT CASE 
                        WHEN NEW.color_count < 2 OR NEW.color_count > 30 THEN
                            RAISE (ABORT, 'Color count must be between 2 and 30')
                    END;
                END;
            """))
        except Exception as e:
            print("Trigger might already exist:", e)
        
        conn.commit()

if __name__ == "__main__":
    migrate() 