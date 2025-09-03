export interface User {
  id: string;
  email: string;
  name: string;
  bio?: string;
  location?: string;
  profilePictureUrl?: string;
  kidAges?: number[];
  interests?: string[];
  availabilityPreference?: 'mornings' | 'afternoons' | 'evenings' | 'weekends' | 'flexible';
  childcareStyle?: 'structured' | 'free-play' | 'educational' | 'outdoor' | 'mixed';
  isSetupComplete: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Activity {
  id: string;
  title: string;
  description: string;
  creatorId: string;
  location: string;
  latitude?: number;
  longitude?: number;
  dateTime: string;
  duration?: number;
  maxParticipants?: number;
  currentParticipants: number;
  category: 'playdate' | 'childcare' | 'educational' | 'outdoor' | 'social' | 'other';
  ageRange?: {
    min: number;
    max: number;
  };
  requirements?: string[];
  isRecurring: boolean;
  recurringPattern?: 'daily' | 'weekly' | 'monthly';
  status: 'active' | 'cancelled' | 'completed';
  createdAt: string;
  updatedAt: string;
}

export interface LoginToken {
  id: string;
  email: string;
  token: string;
  expiresAt: string;
  used: boolean;
  createdAt: string;
}

export interface ActivityParticipant {
  activityId: string;
  userId: string;
  joinedAt: string;
  status: 'confirmed' | 'pending' | 'declined';
}

export interface UserConnection {
  id: string;
  requesterId: string;
  recipientId: string;
  status: 'pending' | 'accepted' | 'declined' | 'blocked';
  createdAt: string;
  updatedAt: string;
}

export interface CreateUserRequest {
  email: string;
  name: string;
  bio?: string;
  location?: string;
  kidAges?: number[];
  interests?: string[];
  availabilityPreference?: 'mornings' | 'afternoons' | 'evenings' | 'weekends' | 'flexible';
  childcareStyle?: 'structured' | 'free-play' | 'educational' | 'outdoor' | 'mixed';
}

export interface CreateActivityRequest {
  title: string;
  description: string;
  location: string;
  latitude?: number;
  longitude?: number;
  dateTime: string;
  duration?: number;
  maxParticipants?: number;
  category: 'playdate' | 'childcare' | 'educational' | 'outdoor' | 'social' | 'other';
  ageRange?: {
    min: number;
    max: number;
  };
  requirements?: string[];
  isRecurring: boolean;
  recurringPattern?: 'daily' | 'weekly' | 'monthly';
}

export interface LoginRequest {
  email: string;
}

export interface VerifyTokenRequest {
  token: string;
}

export interface UpdateUserRequest extends Partial<CreateUserRequest> {
  isSetupComplete?: boolean;
}

export interface ActivityFilters {
  category?: string;
  dateRange?: {
    start: string;
    end: string;
  };
  location?: string;
  maxDistance?: number;
  ageRange?: {
    min: number;
    max: number;
  };
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface UserSetupStep {
  id: string;
  title: string;
  description: string;
  isComplete: boolean;
  isRequired: boolean;
}

export interface NotificationPreferences {
  activityReminders: boolean;
  newConnections: boolean;
  activityInvites: boolean;
  messageNotifications: boolean;
  emailDigest: boolean;
}

export interface SafetySettings {
  profileVisibility: 'public' | 'connections' | 'private';
  locationSharing: 'exact' | 'approximate' | 'none';
  childPhotoSharing: boolean;
  backgroundCheckRequired: boolean;
}

export interface UserProfile extends User {
  connectionCount: number;
  activitiesCreated: number;
  activitiesJoined: number;
  averageRating?: number;
  lastActiveAt: string;
  notificationPreferences: NotificationPreferences;
  safetySettings: SafetySettings;
}