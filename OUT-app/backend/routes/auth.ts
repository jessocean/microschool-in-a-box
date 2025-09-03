import { Hono } from 'hono';
import { DatabaseQueries } from '../database/queries.js';
import { ApiResponse, LoginRequest, VerifyTokenRequest } from '../../shared/types.js';
import * as nodemailer from 'nodemailer';

const auth = new Hono();

// Email transporter (configure with your email service)
const createEmailTransporter = () => {
  // In development, use ethereal email for testing
  // In production, configure with your email service (Gmail, SendGrid, etc.)
  return nodemailer.createTransporter({
    host: process.env.SMTP_HOST || 'smtp.ethereal.email',
    port: parseInt(process.env.SMTP_PORT || '587'),
    secure: false,
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS
    }
  });
};

// Send magic link for login
auth.post('/login', async (c) => {
  try {
    const body: LoginRequest = await c.req.json();
    const dbQueries = c.get('dbQueries') as DatabaseQueries;
    
    // Validate input
    if (!body.email) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Email is required'
      }, 400);
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(body.email)) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Invalid email format'
      }, 400);
    }

    // Check if user exists
    const user = await dbQueries.getUserByEmail(body.email);
    if (!user) {
      return c.json<ApiResponse>({
        success: false,
        error: 'User not found. Please sign up first.'
      }, 404);
    }

    // Generate and store login token
    const loginToken = await dbQueries.createLoginToken(body.email);

    // Create magic link
    const baseUrl = process.env.BASE_URL || `${c.req.url.split('/api')[0]}`;
    const magicLink = `${baseUrl}/login?token=${loginToken.token}`;

    // Send email with magic link
    try {
      if (process.env.NODE_ENV === 'production' && process.env.SMTP_USER) {
        const transporter = createEmailTransporter();
        
        await transporter.sendMail({
          from: process.env.FROM_EMAIL || 'noreply@outapp.com',
          to: body.email,
          subject: 'Your OUT App Login Link',
          html: `
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
              <h2>Welcome back to OUT!</h2>
              <p>Click the link below to log in to your account:</p>
              <a href="${magicLink}" style="display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 16px 0;">
                Log In to OUT
              </a>
              <p>This link will expire in 15 minutes for security.</p>
              <p>If you didn't request this login, you can safely ignore this email.</p>
            </div>
          `
        });
      } else {
        // In development, just log the magic link
        console.log(`\n🔗 Magic link for ${body.email}:`);
        console.log(`${magicLink}\n`);
      }
    } catch (emailError) {
      console.error('Failed to send email:', emailError);
      // Don't fail the request if email sending fails
    }

    return c.json<ApiResponse>({
      success: true,
      data: { 
        message: 'Magic link sent to your email',
        // Include link in development for easier testing
        ...(process.env.NODE_ENV === 'development' && { magicLink })
      }
    });

  } catch (error) {
    console.error('Error sending magic link:', error);
    return c.json<ApiResponse>({
      success: false,
      error: 'Internal server error'
    }, 500);
  }
});

// Verify magic link token
auth.post('/verify', async (c) => {
  try {
    const body: VerifyTokenRequest = await c.req.json();
    const dbQueries = c.get('dbQueries') as DatabaseQueries;
    
    if (!body.token) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Token is required'
      }, 400);
    }

    // Verify and use the token
    const loginToken = await dbQueries.verifyAndUseToken(body.token);
    
    if (!loginToken) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Invalid or expired token'
      }, 401);
    }

    // Get user details
    const user = await dbQueries.getUserByEmail(loginToken.email);
    if (!user) {
      return c.json<ApiResponse>({
        success: false,
        error: 'User not found'
      }, 404);
    }

    // Clean up expired tokens
    await dbQueries.cleanupExpiredTokens();

    // Generate session token (in production, use JWT or proper session management)
    const sessionToken = crypto.randomUUID();

    return c.json<ApiResponse>({
      success: true,
      data: { 
        user,
        sessionToken,
        message: 'Login successful'
      }
    });

  } catch (error) {
    console.error('Error verifying token:', error);
    return c.json<ApiResponse>({
      success: false,
      error: 'Internal server error'
    }, 500);
  }
});

// Logout (invalidate session)
auth.post('/logout', async (c) => {
  try {
    const userId = c.req.header('X-User-ID');
    
    if (!userId) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Not logged in'
      }, 401);
    }

    // In a real implementation, invalidate the session token
    // For now, just return success
    
    return c.json<ApiResponse>({
      success: true,
      data: { message: 'Logged out successfully' }
    });

  } catch (error) {
    console.error('Error logging out:', error);
    return c.json<ApiResponse>({
      success: false,
      error: 'Internal server error'
    }, 500);
  }
});

// Check authentication status
auth.get('/me', async (c) => {
  try {
    const userId = c.req.header('X-User-ID');
    const dbQueries = c.get('dbQueries') as DatabaseQueries;
    
    if (!userId) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Not authenticated'
      }, 401);
    }

    const user = await dbQueries.getUserById(userId);
    if (!user) {
      return c.json<ApiResponse>({
        success: false,
        error: 'User not found'
      }, 404);
    }

    return c.json<ApiResponse>({
      success: true,
      data: { user }
    });

  } catch (error) {
    console.error('Error checking auth status:', error);
    return c.json<ApiResponse>({
      success: false,
      error: 'Internal server error'
    }, 500);
  }
});

// Resend magic link
auth.post('/resend', async (c) => {
  try {
    const { email } = await c.req.json();
    const dbQueries = c.get('dbQueries') as DatabaseQueries;
    
    if (!email) {
      return c.json<ApiResponse>({
        success: false,
        error: 'Email is required'
      }, 400);
    }

    // Check if user exists
    const user = await dbQueries.getUserByEmail(email);
    if (!user) {
      return c.json<ApiResponse>({
        success: false,
        error: 'User not found'
      }, 404);
    }

    // Generate new token
    const loginToken = await dbQueries.createLoginToken(email);

    // Create magic link
    const baseUrl = process.env.BASE_URL || `${c.req.url.split('/api')[0]}`;
    const magicLink = `${baseUrl}/login?token=${loginToken.token}`;

    // Send email (same logic as login endpoint)
    try {
      if (process.env.NODE_ENV === 'production' && process.env.SMTP_USER) {
        const transporter = createEmailTransporter();
        
        await transporter.sendMail({
          from: process.env.FROM_EMAIL || 'noreply@outapp.com',
          to: email,
          subject: 'Your OUT App Login Link (Resent)',
          html: `
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
              <h2>Welcome back to OUT!</h2>
              <p>Here's your requested login link:</p>
              <a href="${magicLink}" style="display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 16px 0;">
                Log In to OUT
              </a>
              <p>This link will expire in 15 minutes for security.</p>
            </div>
          `
        });
      } else {
        console.log(`\n🔗 Resent magic link for ${email}:`);
        console.log(`${magicLink}\n`);
      }
    } catch (emailError) {
      console.error('Failed to resend email:', emailError);
    }

    return c.json<ApiResponse>({
      success: true,
      data: { 
        message: 'Magic link resent to your email',
        ...(process.env.NODE_ENV === 'development' && { magicLink })
      }
    });

  } catch (error) {
    console.error('Error resending magic link:', error);
    return c.json<ApiResponse>({
      success: false,
      error: 'Internal server error'
    }, 500);
  }
});

export default auth;