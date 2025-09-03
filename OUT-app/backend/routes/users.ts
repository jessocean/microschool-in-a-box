import { Hono } from 'hono';
import { DatabaseQueries } from '../database/queries.js';
import { ApiResponse, CreateUserRequest, UpdateUserRequest, User } from '../../shared/types.js';

const users = new Hono();

// Validation helper functions
const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const validateKidAges = (ages: number[]): boolean => {
  return ages.every(age => age >= 0 && age <= 18 && Number.isInteger(age));
};

// Create a new user (signup)
users.post('/', async (c) => {
  try {
    const body: CreateUserRequest = await c.req.json();
    const dbQueries = c.get('dbQueries') as DatabaseQueries;
    
    // Validate required fields
    if (!body.name || !body.email) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Name and email are required'
      }, 400);
    }

    // Validate email format
    if (!validateEmail(body.email)) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Invalid email format'
      }, 400);
    }

    // Validate kid ages if provided
    if (body.kidAges && !validateKidAges(body.kidAges)) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Kid ages must be integers between 0 and 18'
      }, 400);
    }

    // Check if user already exists
    const existingUser = await dbQueries.getUserByEmail(body.email);
    if (existingUser) {
      return c.json<ApiResponse>({
        success: false,
        error: 'User with this email already exists'
      }, 409);
    }

    // Create user
    const user = await dbQueries.createUser(body);

    // Return user data without sensitive information
    const userResponse = {
      id: user.id,
      name: user.name,
      email: user.email,
      bio: user.bio,
      location: user.location,
      kidAges: user.kidAges,
      interests: user.interests,
      availabilityPreference: user.availabilityPreference,
      childcareStyle: user.childcareStyle,
      isSetupComplete: user.isSetupComplete,
      createdAt: user.createdAt
    };

    return c.json<ApiResponse>({
      success: true,
      data: { user: userResponse },
      message: 'User created successfully'
    }, 201);

  } catch (error) {
    console.error('Error creating user:', error);
    return c.json<ApiResponse>({
      success: false,
      error: 'Internal server error'
    }, 500);
  }
});

// Get user profile by ID
users.get('/:userId', async (c) => {
  try {
    const userId = c.req.param('userId');
    const requestingUserId = c.req.header('X-User-ID');
    const dbQueries = c.get('dbQueries') as DatabaseQueries;

    if (!userId) {
      return c.json<ApiResponse>({
        success: false,
        error: 'User ID is required'
      }, 400);
    }

    const user = await dbQueries.getUserById(userId);
    if (!user) {
      return c.json<ApiResponse>({
        success: false,
        error: 'User not found'
      }, 404);
    }

    // If requesting own profile, return full data
    // Otherwise, return limited public data
    let userData;
    if (requestingUserId === userId) {
      userData = user;
    } else {
      // Return public profile data only
      userData = {
        id: user.id,
        name: user.name,
        bio: user.bio,
        location: user.location,
        profilePictureUrl: user.profilePictureUrl,
        kidAges: user.kidAges,
        interests: user.interests,
        availabilityPreference: user.availabilityPreference,
        childcareStyle: user.childcareStyle,
        isSetupComplete: user.isSetupComplete,
        createdAt: user.createdAt
        // Exclude email and other private data
      };
    }

    return c.json<ApiResponse>({
      success: true,
      data: { user: userData }
    });

  } catch (error) {
    console.error('Error fetching user:', error);
    return c.json<ApiResponse>({
      success: false,
      error: 'Internal server error'
    }, 500);
  }
});

// Update user profile
users.put('/:userId', async (c) => {
  try {
    const userId = c.req.param('userId');
    const requestingUserId = c.req.header('X-User-ID');
    const dbQueries = c.get('dbQueries') as DatabaseQueries;
    
    // Users can only update their own profile
    if (requestingUserId !== userId) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Unauthorized: Can only update your own profile'
      }, 403);
    }

    const updates: UpdateUserRequest = await c.req.json();
    
    // Validate email format if email is being updated
    if (updates.email && !validateEmail(updates.email)) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Invalid email format'
      }, 400);
    }

    // Validate kid ages if provided
    if (updates.kidAges && !validateKidAges(updates.kidAges)) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Kid ages must be integers between 0 and 18'
      }, 400);
    }

    // Get current user to verify it exists
    const currentUser = await dbQueries.getUserById(userId);
    if (!currentUser) {
      return c.json<ApiResponse>({
        success: false,
        error: 'User not found'
      }, 404);
    }

    // If email is being updated, check for conflicts
    if (updates.email && updates.email !== currentUser.email) {
      const existingUser = await dbQueries.getUserByEmail(updates.email);
      if (existingUser) {
        return c.json<ApiResponse>({
          success: false,
          error: 'Email already in use by another user'
        }, 409);
      }
    }

    // Update user
    const updatedUser = await dbQueries.updateUser(userId, updates);
    
    if (!updatedUser) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Failed to update user'
      }, 500);
    }

    return c.json<ApiResponse>({
      success: true,
      data: { user: updatedUser },
      message: 'User updated successfully'
    });

  } catch (error) {
    console.error('Error updating user:', error);
    return c.json<ApiResponse>({
      success: false,
      error: 'Internal server error'
    }, 500);
  }
});

// Delete user account
users.delete('/:userId', async (c) => {
  try {
    const userId = c.req.param('userId');
    const requestingUserId = c.req.header('X-User-ID');
    const db = c.get('db');
    
    // Users can only delete their own account
    if (requestingUserId !== userId) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Unauthorized: Can only delete your own account'
      }, 403);
    }

    // Check if user exists
    const dbQueries = c.get('dbQueries') as DatabaseQueries;
    const user = await dbQueries.getUserById(userId);
    if (!user) {
      return c.json<ApiResponse>({
        success: false,
        error: 'User not found'
      }, 404);
    }

    // Delete user (cascading deletes will handle related records)
    return new Promise((resolve) => {
      db.run('DELETE FROM users WHERE id = ?', [userId], function(err: any) {
        if (err) {
          console.error('Error deleting user:', err);
          resolve(c.json<ApiResponse>({
            success: false,
            error: 'Internal server error'
          }, 500));
          return;
        }

        if (this.changes === 0) {
          resolve(c.json<ApiResponse>({
            success: false,
            error: 'User not found'
          }, 404));
          return;
        }

        resolve(c.json<ApiResponse>({
          success: true,
          message: 'User account deleted successfully'
        }));
      });
    });

  } catch (error) {
    console.error('Error deleting user:', error);
    return c.json<ApiResponse>({
      success: false,
      error: 'Internal server error'
    }, 500);
  }
});

// Get user's activities
users.get('/:userId/activities', async (c) => {
  try {
    const userId = c.req.param('userId');
    const requestingUserId = c.req.header('X-User-ID');
    const dbQueries = c.get('dbQueries') as DatabaseQueries;

    if (!userId) {
      return c.json<ApiResponse>({
        success: false,
        error: 'User ID is required'
      }, 400);
    }

    // Check if user exists
    const user = await dbQueries.getUserById(userId);
    if (!user) {
      return c.json<ApiResponse>({
        success: false,
        error: 'User not found'
      }, 404);
    }

    // Get activities created by the user
    const activities = await dbQueries.getActivitiesByCreator(userId);

    // If requesting someone else's activities, only return public information
    let activitiesData = activities;
    if (requestingUserId !== userId) {
      activitiesData = activities.map(activity => ({
        ...activity,
        // Remove any private fields if needed
      }));
    }

    return c.json<ApiResponse>({
      success: true,
      data: { activities: activitiesData }
    });

  } catch (error) {
    console.error('Error fetching user activities:', error);
    return c.json<ApiResponse>({
      success: false,
      error: 'Internal server error'
    }, 500);
  }
});

// Search users by criteria
users.get('/', async (c) => {
  try {
    const searchQuery = c.req.query('q');
    const location = c.req.query('location');
    const interests = c.req.query('interests');
    const childcareStyle = c.req.query('childcareStyle');
    const limit = parseInt(c.req.query('limit') || '20');
    const offset = parseInt(c.req.query('offset') || '0');
    const db = c.get('db');

    // Build dynamic search query
    let query = 'SELECT id, name, bio, location, kid_ages, interests, availability_preference, childcare_style, is_setup_complete, created_at FROM users WHERE 1=1';
    const params: any[] = [];

    if (searchQuery) {
      query += ' AND (name LIKE ? OR bio LIKE ?)';
      params.push(`%${searchQuery}%`, `%${searchQuery}%`);
    }

    if (location) {
      query += ' AND location LIKE ?';
      params.push(`%${location}%`);
    }

    if (childcareStyle) {
      query += ' AND childcare_style = ?';
      params.push(childcareStyle);
    }

    if (interests) {
      const interestList = interests.split(',');
      const interestConditions = interestList.map(() => 'interests LIKE ?').join(' OR ');
      query += ` AND (${interestConditions})`;
      interestList.forEach(interest => params.push(`%${interest.trim()}%`));
    }

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
    params.push(limit, offset);

    return new Promise((resolve) => {
      db.all(query, params, (err: any, rows: any[]) => {
        if (err) {
          console.error('Error searching users:', err);
          resolve(c.json<ApiResponse>({
            success: false,
            error: 'Internal server error'
          }, 500));
          return;
        }

        const users = rows.map(row => ({
          id: row.id,
          name: row.name,
          bio: row.bio,
          location: row.location,
          kidAges: row.kid_ages ? JSON.parse(row.kid_ages) : undefined,
          interests: row.interests ? JSON.parse(row.interests) : undefined,
          availabilityPreference: row.availability_preference,
          childcareStyle: row.childcare_style,
          isSetupComplete: Boolean(row.is_setup_complete),
          createdAt: row.created_at
        }));

        resolve(c.json<ApiResponse>({
          success: true,
          data: { users }
        }));
      });
    });

  } catch (error) {
    console.error('Error searching users:', error);
    return c.json<ApiResponse>({
      success: false,
      error: 'Internal server error'
    }, 500);
  }
});

export default users;