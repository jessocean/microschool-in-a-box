import Database from 'sqlite3';

export function initializeDatabase(db: Database.Database): Promise<void> {
  return new Promise((resolve, reject) => {
    const migrations = [
      `CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        bio TEXT,
        location TEXT,
        profile_picture_url TEXT,
        kid_ages TEXT, -- JSON array of ages
        interests TEXT, -- JSON array of interests
        availability_preference TEXT CHECK (availability_preference IN ('mornings', 'afternoons', 'evenings', 'weekends', 'flexible')),
        childcare_style TEXT CHECK (childcare_style IN ('structured', 'free-play', 'educational', 'outdoor', 'mixed')),
        is_setup_complete BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )`,
      
      `CREATE TABLE IF NOT EXISTS activities (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        creator_id TEXT NOT NULL,
        location TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        date_time DATETIME NOT NULL,
        duration INTEGER, -- duration in minutes
        max_participants INTEGER,
        current_participants INTEGER DEFAULT 0,
        category TEXT NOT NULL CHECK (category IN ('playdate', 'childcare', 'educational', 'outdoor', 'social', 'other')),
        age_range_min INTEGER,
        age_range_max INTEGER,
        requirements TEXT, -- JSON array
        is_recurring BOOLEAN DEFAULT FALSE,
        recurring_pattern TEXT CHECK (recurring_pattern IN ('daily', 'weekly', 'monthly')),
        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'completed')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (creator_id) REFERENCES users (id) ON DELETE CASCADE
      )`,
      
      `CREATE TABLE IF NOT EXISTS login_tokens (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        token TEXT UNIQUE NOT NULL,
        expires_at DATETIME NOT NULL,
        used BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )`,
      
      `CREATE TABLE IF NOT EXISTS activity_participants (
        activity_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'pending', 'declined')),
        PRIMARY KEY (activity_id, user_id),
        FOREIGN KEY (activity_id) REFERENCES activities (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
      )`,
      
      `CREATE TABLE IF NOT EXISTS user_connections (
        id TEXT PRIMARY KEY,
        requester_id TEXT NOT NULL,
        recipient_id TEXT NOT NULL,
        status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'blocked')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (requester_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (recipient_id) REFERENCES users (id) ON DELETE CASCADE,
        UNIQUE(requester_id, recipient_id)
      )`,
      
      // Indexes for better performance
      `CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)`,
      `CREATE INDEX IF NOT EXISTS idx_activities_creator ON activities (creator_id)`,
      `CREATE INDEX IF NOT EXISTS idx_activities_date ON activities (date_time)`,
      `CREATE INDEX IF NOT EXISTS idx_activities_location ON activities (latitude, longitude)`,
      `CREATE INDEX IF NOT EXISTS idx_login_tokens_token ON login_tokens (token)`,
      `CREATE INDEX IF NOT EXISTS idx_login_tokens_email ON login_tokens (email)`,
      `CREATE INDEX IF NOT EXISTS idx_activity_participants_activity ON activity_participants (activity_id)`,
      `CREATE INDEX IF NOT EXISTS idx_activity_participants_user ON activity_participants (user_id)`,
      `CREATE INDEX IF NOT EXISTS idx_user_connections_requester ON user_connections (requester_id)`,
      `CREATE INDEX IF NOT EXISTS idx_user_connections_recipient ON user_connections (recipient_id)`,
      
      // Triggers to update timestamps
      `CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
       AFTER UPDATE ON users
       BEGIN
         UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
       END`,
       
      `CREATE TRIGGER IF NOT EXISTS update_activities_timestamp 
       AFTER UPDATE ON activities
       BEGIN
         UPDATE activities SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
       END`,
       
      `CREATE TRIGGER IF NOT EXISTS update_connections_timestamp 
       AFTER UPDATE ON user_connections
       BEGIN
         UPDATE user_connections SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
       END`
    ];

    let completed = 0;
    const total = migrations.length;

    if (total === 0) {
      resolve();
      return;
    }

    migrations.forEach((migration) => {
      db.run(migration, (err) => {
        if (err) {
          console.error('Migration error:', err);
          reject(err);
          return;
        }
        
        completed++;
        if (completed === total) {
          console.log('Database migrations completed successfully');
          resolve();
        }
      });
    });
  });
}

export function dropAllTables(db: Database.Database): Promise<void> {
  return new Promise((resolve, reject) => {
    const dropStatements = [
      'DROP TABLE IF EXISTS user_connections',
      'DROP TABLE IF EXISTS activity_participants', 
      'DROP TABLE IF EXISTS login_tokens',
      'DROP TABLE IF EXISTS activities',
      'DROP TABLE IF EXISTS users'
    ];

    let completed = 0;
    const total = dropStatements.length;

    dropStatements.forEach((statement) => {
      db.run(statement, (err) => {
        if (err) {
          reject(err);
          return;
        }
        
        completed++;
        if (completed === total) {
          resolve();
        }
      });
    });
  });
}