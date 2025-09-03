import Database from 'sqlite3';
import { User, Activity, LoginToken, CreateUserRequest, CreateActivityRequest, UpdateUserRequest } from '../../shared/types.js';

export class DatabaseQueries {
  constructor(private db: Database.Database) {}

  // User queries
  async createUser(userData: CreateUserRequest): Promise<User> {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    
    return new Promise((resolve, reject) => {
      const stmt = this.db.prepare(`
        INSERT INTO users (
          id, email, name, bio, location, kid_ages, interests,
          availability_preference, childcare_style, is_setup_complete,
          created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);

      stmt.run([
        id,
        userData.email,
        userData.name,
        userData.bio || null,
        userData.location || null,
        userData.kidAges ? JSON.stringify(userData.kidAges) : null,
        userData.interests ? JSON.stringify(userData.interests) : null,
        userData.availabilityPreference || null,
        userData.childcareStyle || null,
        false,
        now,
        now
      ], function(err) {
        if (err) {
          reject(err);
          return;
        }

        const user: User = {
          id,
          email: userData.email,
          name: userData.name,
          bio: userData.bio,
          location: userData.location,
          kidAges: userData.kidAges,
          interests: userData.interests,
          availabilityPreference: userData.availabilityPreference,
          childcareStyle: userData.childcareStyle,
          isSetupComplete: false,
          createdAt: now,
          updatedAt: now
        };

        resolve(user);
      });

      stmt.finalize();
    });
  }

  async getUserByEmail(email: string): Promise<User | null> {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM users WHERE email = ?',
        [email],
        (err, row: any) => {
          if (err) {
            reject(err);
            return;
          }

          if (!row) {
            resolve(null);
            return;
          }

          const user: User = {
            id: row.id,
            email: row.email,
            name: row.name,
            bio: row.bio,
            location: row.location,
            profilePictureUrl: row.profile_picture_url,
            kidAges: row.kid_ages ? JSON.parse(row.kid_ages) : undefined,
            interests: row.interests ? JSON.parse(row.interests) : undefined,
            availabilityPreference: row.availability_preference,
            childcareStyle: row.childcare_style,
            isSetupComplete: Boolean(row.is_setup_complete),
            createdAt: row.created_at,
            updatedAt: row.updated_at
          };

          resolve(user);
        }
      );
    });
  }

  async getUserById(id: string): Promise<User | null> {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM users WHERE id = ?',
        [id],
        (err, row: any) => {
          if (err) {
            reject(err);
            return;
          }

          if (!row) {
            resolve(null);
            return;
          }

          const user: User = {
            id: row.id,
            email: row.email,
            name: row.name,
            bio: row.bio,
            location: row.location,
            profilePictureUrl: row.profile_picture_url,
            kidAges: row.kid_ages ? JSON.parse(row.kid_ages) : undefined,
            interests: row.interests ? JSON.parse(row.interests) : undefined,
            availabilityPreference: row.availability_preference,
            childcareStyle: row.childcare_style,
            isSetupComplete: Boolean(row.is_setup_complete),
            createdAt: row.created_at,
            updatedAt: row.updated_at
          };

          resolve(user);
        }
      );
    });
  }

  async updateUser(id: string, updates: UpdateUserRequest): Promise<User | null> {
    const setClause: string[] = [];
    const values: any[] = [];

    Object.entries(updates).forEach(([key, value]) => {
      if (value !== undefined) {
        if (key === 'kidAges' || key === 'interests') {
          setClause.push(`${key.replace(/([A-Z])/g, '_$1').toLowerCase()} = ?`);
          values.push(JSON.stringify(value));
        } else if (key === 'isSetupComplete') {
          setClause.push('is_setup_complete = ?');
          values.push(value);
        } else if (key === 'availabilityPreference') {
          setClause.push('availability_preference = ?');
          values.push(value);
        } else if (key === 'childcareStyle') {
          setClause.push('childcare_style = ?');
          values.push(value);
        } else {
          setClause.push(`${key} = ?`);
          values.push(value);
        }
      }
    });

    if (setClause.length === 0) {
      return this.getUserById(id);
    }

    values.push(id);

    return new Promise((resolve, reject) => {
      const query = `UPDATE users SET ${setClause.join(', ')} WHERE id = ?`;
      
      this.db.run(query, values, function(err) {
        if (err) {
          reject(err);
          return;
        }

        if (this.changes === 0) {
          resolve(null);
          return;
        }

        // Return updated user
        resolve(null); // Will be handled by getUserById call
      });
    }).then(() => this.getUserById(id));
  }

  // Activity queries
  async createActivity(activityData: CreateActivityRequest, creatorId: string): Promise<Activity> {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();

    return new Promise((resolve, reject) => {
      const stmt = this.db.prepare(`
        INSERT INTO activities (
          id, title, description, creator_id, location, latitude, longitude,
          date_time, duration, max_participants, category, age_range_min, age_range_max,
          requirements, is_recurring, recurring_pattern, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);

      stmt.run([
        id,
        activityData.title,
        activityData.description,
        creatorId,
        activityData.location,
        activityData.latitude || null,
        activityData.longitude || null,
        activityData.dateTime,
        activityData.duration || null,
        activityData.maxParticipants || null,
        activityData.category,
        activityData.ageRange?.min || null,
        activityData.ageRange?.max || null,
        activityData.requirements ? JSON.stringify(activityData.requirements) : null,
        activityData.isRecurring,
        activityData.recurringPattern || null,
        now,
        now
      ], function(err) {
        if (err) {
          reject(err);
          return;
        }

        const activity: Activity = {
          id,
          title: activityData.title,
          description: activityData.description,
          creatorId,
          location: activityData.location,
          latitude: activityData.latitude,
          longitude: activityData.longitude,
          dateTime: activityData.dateTime,
          duration: activityData.duration,
          maxParticipants: activityData.maxParticipants,
          currentParticipants: 0,
          category: activityData.category,
          ageRange: activityData.ageRange,
          requirements: activityData.requirements,
          isRecurring: activityData.isRecurring,
          recurringPattern: activityData.recurringPattern,
          status: 'active',
          createdAt: now,
          updatedAt: now
        };

        resolve(activity);
      });

      stmt.finalize();
    });
  }

  async getActivitiesByCreator(creatorId: string): Promise<Activity[]> {
    return new Promise((resolve, reject) => {
      this.db.all(
        'SELECT * FROM activities WHERE creator_id = ? ORDER BY date_time ASC',
        [creatorId],
        (err, rows: any[]) => {
          if (err) {
            reject(err);
            return;
          }

          const activities: Activity[] = rows.map(row => ({
            id: row.id,
            title: row.title,
            description: row.description,
            creatorId: row.creator_id,
            location: row.location,
            latitude: row.latitude,
            longitude: row.longitude,
            dateTime: row.date_time,
            duration: row.duration,
            maxParticipants: row.max_participants,
            currentParticipants: row.current_participants,
            category: row.category,
            ageRange: row.age_range_min && row.age_range_max ? {
              min: row.age_range_min,
              max: row.age_range_max
            } : undefined,
            requirements: row.requirements ? JSON.parse(row.requirements) : undefined,
            isRecurring: Boolean(row.is_recurring),
            recurringPattern: row.recurring_pattern,
            status: row.status,
            createdAt: row.created_at,
            updatedAt: row.updated_at
          }));

          resolve(activities);
        }
      );
    });
  }

  async getNearbyActivities(latitude: number, longitude: number, radiusKm: number = 10): Promise<Activity[]> {
    return new Promise((resolve, reject) => {
      const query = `
        SELECT * FROM activities 
        WHERE latitude IS NOT NULL 
        AND longitude IS NOT NULL 
        AND status = 'active'
        AND date_time > datetime('now')
        AND (
          6371 * acos(
            cos(radians(?)) * cos(radians(latitude)) * 
            cos(radians(longitude) - radians(?)) + 
            sin(radians(?)) * sin(radians(latitude))
          )
        ) <= ?
        ORDER BY date_time ASC
      `;

      this.db.all(
        query,
        [latitude, longitude, latitude, radiusKm],
        (err, rows: any[]) => {
          if (err) {
            reject(err);
            return;
          }

          const activities: Activity[] = rows.map(row => ({
            id: row.id,
            title: row.title,
            description: row.description,
            creatorId: row.creator_id,
            location: row.location,
            latitude: row.latitude,
            longitude: row.longitude,
            dateTime: row.date_time,
            duration: row.duration,
            maxParticipants: row.max_participants,
            currentParticipants: row.current_participants,
            category: row.category,
            ageRange: row.age_range_min && row.age_range_max ? {
              min: row.age_range_min,
              max: row.age_range_max
            } : undefined,
            requirements: row.requirements ? JSON.parse(row.requirements) : undefined,
            isRecurring: Boolean(row.is_recurring),
            recurringPattern: row.recurring_pattern,
            status: row.status,
            createdAt: row.created_at,
            updatedAt: row.updated_at
          }));

          resolve(activities);
        }
      );
    });
  }

  // Login token queries
  async createLoginToken(email: string): Promise<LoginToken> {
    const id = crypto.randomUUID();
    const token = crypto.randomUUID().replace(/-/g, '');
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000).toISOString(); // 15 minutes
    const now = new Date().toISOString();

    return new Promise((resolve, reject) => {
      const stmt = this.db.prepare(`
        INSERT INTO login_tokens (id, email, token, expires_at, created_at)
        VALUES (?, ?, ?, ?, ?)
      `);

      stmt.run([id, email, token, expiresAt, now], function(err) {
        if (err) {
          reject(err);
          return;
        }

        const loginToken: LoginToken = {
          id,
          email,
          token,
          expiresAt,
          used: false,
          createdAt: now
        };

        resolve(loginToken);
      });

      stmt.finalize();
    });
  }

  async verifyAndUseToken(token: string): Promise<LoginToken | null> {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM login_tokens WHERE token = ? AND used = 0 AND expires_at > datetime("now")',
        [token],
        (err, row: any) => {
          if (err) {
            reject(err);
            return;
          }

          if (!row) {
            resolve(null);
            return;
          }

          // Mark token as used
          this.db.run(
            'UPDATE login_tokens SET used = 1 WHERE id = ?',
            [row.id],
            (updateErr) => {
              if (updateErr) {
                reject(updateErr);
                return;
              }

              const loginToken: LoginToken = {
                id: row.id,
                email: row.email,
                token: row.token,
                expiresAt: row.expires_at,
                used: true,
                createdAt: row.created_at
              };

              resolve(loginToken);
            }
          );
        }
      );
    });
  }

  async cleanupExpiredTokens(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.db.run(
        'DELETE FROM login_tokens WHERE expires_at < datetime("now")',
        (err) => {
          if (err) {
            reject(err);
            return;
          }
          resolve();
        }
      );
    });
  }
}