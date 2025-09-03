const { useState, useEffect } = React;

interface AppState {
  currentUser: any;
  isAuthenticated: boolean;
  currentView: 'login' | 'setup' | 'dashboard';
  loading: boolean;
}

const App: React.FC = () => {
  const [state, setState] = useState<AppState>({
    currentUser: null,
    isAuthenticated: false,
    currentView: 'login',
    loading: true
  });

  useEffect(() => {
    // Check for existing session on app load
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const sessionToken = localStorage.getItem('sessionToken');
      if (sessionToken) {
        // In a real app, validate the session token with the backend
        const userData = localStorage.getItem('userData');
        if (userData) {
          const user = JSON.parse(userData);
          setState(prev => ({
            ...prev,
            currentUser: user,
            isAuthenticated: true,
            currentView: 'dashboard',
            loading: false
          }));
          return;
        }
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
    }
    
    setState(prev => ({ ...prev, loading: false }));
  };

  const handleLoginSuccess = (user: any) => {
    setState(prev => ({
      ...prev,
      currentUser: user,
      isAuthenticated: true,
      currentView: user.bio ? 'dashboard' : 'setup'
    }));
    
    localStorage.setItem('userData', JSON.stringify(user));
    localStorage.setItem('sessionToken', 'temp-session-token');
  };

  const handleUserSetupComplete = (user: any) => {
    setState(prev => ({
      ...prev,
      currentUser: user,
      currentView: 'dashboard'
    }));
    
    localStorage.setItem('userData', JSON.stringify(user));
  };

  const handleLogout = () => {
    localStorage.removeItem('userData');
    localStorage.removeItem('sessionToken');
    setState({
      currentUser: null,
      isAuthenticated: false,
      currentView: 'login',
      loading: false
    });
  };

  if (state.loading) {
    return (
      <div className="app">
        <div className="loading">
          <h2>Loading OUT app...</h2>
          <p>Connecting families in your neighborhood</p>
        </div>
      </div>
    );
  }

  const renderCurrentView = () => {
    switch (state.currentView) {
      case 'login':
        return React.createElement(Login, {
          onLoginSuccess: handleLoginSuccess
        });
      
      case 'setup':
        return React.createElement(UserSetup, {
          currentUser: state.currentUser,
          onUserSetupComplete: handleUserSetupComplete
        });
      
      case 'dashboard':
        return React.createElement(Dashboard, {
          currentUser: state.currentUser,
          onLogout: handleLogout
        });
      
      default:
        return React.createElement(Login, {
          onLoginSuccess: handleLoginSuccess
        });
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>OUT</h1>
        <p>Building connections in your neighborhood</p>
        {state.isAuthenticated && (
          <div style={{ position: 'absolute', top: '1rem', right: '2rem' }}>
            <button className="btn btn-secondary" onClick={handleLogout}>
              Logout
            </button>
          </div>
        )}
      </header>
      
      <main className="main">
        {renderCurrentView()}
      </main>
    </div>
  );
};

// Dashboard component
const Dashboard: React.FC<{ currentUser: any; onLogout: () => void }> = ({ currentUser }) => {
  const [activeTab, setActiveTab] = useState('activities');

  const renderTabContent = () => {
    switch (activeTab) {
      case 'activities':
        return React.createElement(ActivityList, { currentUser });
      case 'create':
        return React.createElement(CreateActivity, { currentUser });
      case 'friends':
        return React.createElement(FriendsManager, { currentUser });
      default:
        return React.createElement(ActivityList, { currentUser });
    }
  };

  return (
    <div>
      <div className="card">
        <h2>Welcome back, {currentUser?.name}!</h2>
        <p>What would you like to do today?</p>
        
        <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button 
            className={`btn ${activeTab === 'activities' ? '' : 'btn-secondary'}`}
            onClick={() => setActiveTab('activities')}
          >
            Browse Activities
          </button>
          <button 
            className={`btn ${activeTab === 'create' ? '' : 'btn-secondary'}`}
            onClick={() => setActiveTab('create')}
          >
            Create Activity
          </button>
          <button 
            className={`btn ${activeTab === 'friends' ? '' : 'btn-secondary'}`}
            onClick={() => setActiveTab('friends')}
          >
            Manage Connections
          </button>
        </div>
      </div>

      {renderTabContent()}
    </div>
  );
};

// Simple placeholder components that would be implemented in separate files
const Login: React.FC<{ onLoginSuccess: (user: any) => void }> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // For demo purposes, simulate successful login
      setTimeout(() => {
        const mockUser = {
          userId: '123',
          name: 'Demo User',
          email: email,
          location: { lat: 40.7128, lon: -74.0060, address: 'New York, NY' },
          bio: 'Welcome to OUT!'
        };
        onLoginSuccess(mockUser);
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      setError('Login failed. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: '500px', margin: '0 auto' }}>
      <h2>Welcome to OUT</h2>
      <p>Connect with families in your neighborhood</p>
      
      {error && <div className="error">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="email">Email Address</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="Enter your email"
          />
        </div>
        
        <button type="submit" className="btn" disabled={isLoading}>
          {isLoading ? 'Sending Magic Link...' : 'Send Magic Link'}
        </button>
      </form>
      
      <p style={{ marginTop: '1rem', fontSize: '0.875rem', color: '#6c757d' }}>
        We'll send you a secure login link via email. No password required!
      </p>
    </div>
  );
};

const UserSetup: React.FC<{ currentUser: any; onUserSetupComplete: (user: any) => void }> = ({ 
  currentUser, 
  onUserSetupComplete 
}) => {
  return (
    <div className="card">
      <h2>Complete Your Profile</h2>
      <p>Help us connect you with the right families and activities</p>
      <button 
        className="btn" 
        onClick={() => onUserSetupComplete(currentUser)}
      >
        Skip for Now
      </button>
    </div>
  );
};

const ActivityList: React.FC<{ currentUser: any }> = () => {
  const mockActivities = [
    {
      activityId: '1',
      type: 'open_door',
      title: 'Afternoon Playdate',
      description: 'Kids can play in our backyard while parents chat',
      location: '123 Main St',
      creatorName: 'Sarah Johnson'
    },
    {
      activityId: '2',
      type: 'public_outing',
      title: 'Park Meetup',
      description: 'Meet at Central Park for outdoor fun',
      location: 'Central Park',
      creatorName: 'Mike Chen'
    }
  ];

  return (
    <div>
      <h2>Available Activities</h2>
      {mockActivities.map(activity => (
        <div key={activity.activityId} className="activity-item">
          <span className={`activity-type ${activity.type.replace('_', '-')}`}>
            {activity.type.replace('_', ' ').toUpperCase()}
          </span>
          <h3>{activity.title}</h3>
          <p>{activity.description}</p>
          <p><strong>Location:</strong> {activity.location}</p>
          <p><strong>Host:</strong> {activity.creatorName}</p>
        </div>
      ))}
    </div>
  );
};

const CreateActivity: React.FC<{ currentUser: any }> = () => {
  return (
    <div className="card">
      <h2>Create New Activity</h2>
      <p>Share an opportunity with your neighbors</p>
      <div className="form-group">
        <label>Activity Type</label>
        <select>
          <option value="open_door">Open Door (at your home)</option>
          <option value="public_outing">Public Outing</option>
          <option value="private_outing">Private Outing</option>
        </select>
      </div>
      <div className="form-group">
        <label>Title</label>
        <input type="text" placeholder="What's the activity?" />
      </div>
      <div className="form-group">
        <label>Description</label>
        <textarea placeholder="Tell families what to expect..." />
      </div>
      <button className="btn">Create Activity</button>
    </div>
  );
};

const FriendsManager: React.FC<{ currentUser: any }> = () => {
  return (
    <div className="card">
      <h2>Your Connections</h2>
      <p>Manage your neighborhood network</p>
      <div style={{ textAlign: 'center', padding: '2rem', color: '#6c757d' }}>
        <p>No connections yet. Start by joining some activities!</p>
      </div>
    </div>
  );
};

// Render the app
ReactDOM.render(React.createElement(App), document.getElementById('root'));