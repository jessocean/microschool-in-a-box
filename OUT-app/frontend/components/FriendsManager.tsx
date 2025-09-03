const { useState, useEffect } = React;

interface FriendsManagerProps {
  currentUser: any;
  onFriendsUpdate?: () => void;
}

const FriendsManager: React.FC<FriendsManagerProps> = ({ currentUser, onFriendsUpdate }) => {
  const [connections, setConnections] = useState([]);
  const [nearbyUsers, setNearbyUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'connections' | 'discover'>('connections');
  const [searchRadius, setSearchRadius] = useState(2);

  useEffect(() => {
    if (activeTab === 'connections') {
      fetchConnections();
    } else {
      discoverNearbyUsers();
    }
  }, [activeTab, searchRadius]);

  const fetchConnections = async () => {
    try {
      setLoading(true);
      setError('');
      
      // In a real app, this would fetch the user's actual connections
      // For now, we'll show mock data
      setConnections([]);
    } catch (error) {
      setError('Failed to load connections');
    } finally {
      setLoading(false);
    }
  };

  const discoverNearbyUsers = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await fetch(
        `/api/discovery/users?maxDistance=${searchRadius}`,
        {
          headers: {
            'X-User-ID': currentUser.userId
          }
        }
      );

      const data = await response.json();

      if (data.success) {
        setNearbyUsers(data.data.users || []);
      } else {
        setError(data.error || 'Failed to discover nearby users');
      }
    } catch (error) {
      setError('Network error. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const sendConnectionRequest = async (userId: string) => {
    try {
      // In a real app, this would send a connection request
      console.log(`Sending connection request to user ${userId}`);
      
      // For demo purposes, show success message
      alert('Connection request sent!');
    } catch (error) {
      console.error('Failed to send connection request:', error);
    }
  };

  const formatDistance = (distance: number) => {
    if (distance < 0.1) {
      return '< 0.1 miles away';
    }
    return `${distance} ${distance === 1 ? 'mile' : 'miles'} away`;
  };

  const getCommonInterests = (user: any) => {
    const common = [];
    
    // Check for common kids ages
    const commonAges = user.kidsAges?.filter((age: string) => 
      currentUser.kidsAges?.includes(age)
    ) || [];
    
    // Check for common activity preferences
    const commonActivities = user.activityPreferences?.filter((pref: string) => 
      currentUser.activityPreferences?.includes(pref)
    ) || [];
    
    // Check for common social circle types
    const commonSocial = user.socialCircleTypes?.filter((type: string) => 
      currentUser.socialCircleTypes?.includes(type)
    ) || [];

    if (commonAges.length > 0) {
      common.push(`Kids: ${commonAges.join(', ')}`);
    }
    if (commonActivities.length > 0) {
      common.push(`Activities: ${commonActivities.join(', ')}`);
    }
    if (commonSocial.length > 0) {
      common.push(`Social: ${commonSocial.join(', ')}`);
    }

    return common;
  };

  const renderConnectionsTab = () => {
    if (loading) {
      return (
        <div className="loading">
          <h3>Loading your connections...</h3>
        </div>
      );
    }

    if (connections.length === 0) {
      return (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#6c757d' }}>
          <h3>No connections yet</h3>
          <p>Start by discovering families in your area or joining some activities!</p>
          <button 
            className="btn" 
            onClick={() => setActiveTab('discover')}
            style={{ marginTop: '1rem' }}
          >
            Discover Nearby Families
          </button>
        </div>
      );
    }

    return (
      <div>
        {connections.map((connection: any) => (
          <div key={connection.userId} className="activity-item">
            <h3>{connection.name}</h3>
            <p>{connection.bio}</p>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
              <button className="btn btn-secondary" style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}>
                Message
              </button>
              <button className="btn btn-secondary" style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}>
                View Profile
              </button>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderDiscoverTab = () => {
    if (loading) {
      return (
        <div className="loading">
          <h3>Discovering nearby families...</h3>
        </div>
      );
    }

    if (nearbyUsers.length === 0) {
      return (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#6c757d' }}>
          <h3>No families found nearby</h3>
          <p>Try expanding your search radius or check back later!</p>
          <button 
            className="btn" 
            onClick={() => setSearchRadius(prev => Math.min(prev + 1, 10))}
            style={{ marginTop: '1rem' }}
          >
            Expand Search to {Math.min(searchRadius + 1, 10)} miles
          </button>
        </div>
      );
    }

    return (
      <div>
        {nearbyUsers.map((user: any) => {
          const commonInterests = getCommonInterests(user);
          
          return (
            <div key={user.userId} className="activity-item">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div>
                  <h3 style={{ marginBottom: '0.5rem' }}>{user.name}</h3>
                  <p style={{ fontSize: '0.875rem', color: '#666', margin: '0' }}>
                    {formatDistance(user.distance)}
                  </p>
                </div>
                <button 
                  className="btn"
                  onClick={() => sendConnectionRequest(user.userId)}
                  style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
                >
                  Connect
                </button>
              </div>

              {user.bio && (
                <p style={{ marginBottom: '1rem', color: '#666' }}>{user.bio}</p>
              )}

              {user.kidsAges && user.kidsAges.length > 0 && (
                <div style={{ marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                  <strong>Kids: </strong>
                  <span style={{ color: '#666' }}>{user.kidsAges.join(', ')}</span>
                </div>
              )}

              {user.activityPreferences && user.activityPreferences.length > 0 && (
                <div style={{ marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                  <strong>Interests: </strong>
                  <span style={{ color: '#666' }}>{user.activityPreferences.join(', ')}</span>
                </div>
              )}

              {commonInterests.length > 0 && (
                <div style={{ 
                  marginTop: '1rem', 
                  padding: '0.75rem', 
                  backgroundColor: '#e8f5e8', 
                  borderRadius: '6px',
                  fontSize: '0.875rem'
                }}>
                  <strong style={{ color: '#2d5a2d' }}>You have in common: </strong>
                  <div style={{ color: '#2d5a2d', marginTop: '0.25rem' }}>
                    {commonInterests.map((interest, index) => (
                      <div key={index}>• {interest}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div>
      <div className="card">
        <h2>Your Network</h2>
        <p>Connect with families in your neighborhood</p>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem', marginBottom: '2rem' }}>
          <button
            className={`btn ${activeTab === 'connections' ? '' : 'btn-secondary'}`}
            onClick={() => setActiveTab('connections')}
          >
            My Connections
          </button>
          <button
            className={`btn ${activeTab === 'discover' ? '' : 'btn-secondary'}`}
            onClick={() => setActiveTab('discover')}
          >
            Discover Families
          </button>
        </div>

        {/* Search Radius Control for Discover Tab */}
        {activeTab === 'discover' && (
          <div style={{ marginBottom: '2rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500' }}>
              Search within {searchRadius} {searchRadius === 1 ? 'mile' : 'miles'}
            </label>
            <input
              type="range"
              min="1"
              max="10"
              value={searchRadius}
              onChange={(e) => setSearchRadius(parseInt(e.target.value))}
              style={{ width: '200px' }}
            />
            <div style={{ fontSize: '0.75rem', color: '#6c757d', marginTop: '0.25rem' }}>
              1 mile ← → 10 miles
            </div>
          </div>
        )}

        {error && <div className="error">{error}</div>}
      </div>

      {activeTab === 'connections' ? renderConnectionsTab() : renderDiscoverTab()}
    </div>
  );
};