// Frontend entry point for OUT app
// This file serves as the main entry for the React application

// Import statements would go here in a real TypeScript setup
// import React from 'react';
// import ReactDOM from 'react-dom/client';
// import App from './components/App';

// For this browser-based setup using CDN React, 
// the main App component is loaded directly in index.html

// Export types for use across the frontend
export type { 
  User, 
  Activity, 
  ApiResponse,
  ActivityListProps,
  CreateActivityProps,
  UserSetupProps,
  FriendsManagerProps,
  LoginProps
} from '../shared/types';

// Utility functions for frontend
export const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch {
    return dateString;
  }
};

export const formatTime = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateString;
  }
};

export const formatDistance = (distance: number): string => {
  if (distance < 0.1) {
    return '< 0.1 miles';
  }
  return `${distance.toFixed(1)} ${distance === 1 ? 'mile' : 'miles'}`;
};

// API helper functions
export const apiRequest = async (
  endpoint: string, 
  options: RequestInit = {}
): Promise<any> => {
  const url = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const mergedOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, mergedOptions);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`);
    }
    
    return data;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

// Local storage helpers
export const storage = {
  get: (key: string) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  },
  
  set: (key: string, value: any) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
    }
  },
  
  remove: (key: string) => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Failed to remove from localStorage:', error);
    }
  },
  
  clear: () => {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('Failed to clear localStorage:', error);
    }
  }
};

// Constants
export const APP_CONFIG = {
  name: 'OUT',
  description: 'Building connections in your neighborhood',
  version: '1.0.0',
  defaultSearchRadius: 5,
  maxSearchRadius: 10,
  sessionStorageKey: 'out_session',
  userStorageKey: 'out_user_data'
};

// Initialize app when DOM is ready
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log('OUT app frontend initialized');
  });
}