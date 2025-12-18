-- Add hashed_pin column to children table
ALTER TABLE children ADD COLUMN IF NOT EXISTS hashed_pin VARCHAR(255);

-- For any existing children without hashed_pin, set a temporary one
UPDATE children SET hashed_pin = '$2b$12$temp' WHERE hashed_pin IS NULL;

-- Make it NOT NULL after setting defaults
ALTER TABLE children ALTER COLUMN hashed_pin SET NOT NULL;
