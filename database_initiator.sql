-- Check if the 'logs' table exists and drop it if necessary
DROP TABLE IF EXISTS logs;

-- Create the 'logs' table with the correct schema
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Optionally, you can insert any existing log data here (if needed)
-- INSERT INTO logs (session_id, message) VALUES (1, 'Initial log entry');
