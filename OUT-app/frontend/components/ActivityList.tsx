const { useState, useEffect } = React;

interface ActivityListProps {
  currentUser: any;
  onActivitySelect?: (activity: any) => void;
}

const ActivityList: React.FC<ActivityListProps> = ({ currentUser, onActivitySelect }) => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchActivities();
  }, [currentUser]);

  const fetchActivities = async () => {
    try {
      setLoading(true);
      setError('');

      // Fetch nearby activities
      const response = await fetch(
        `/api/activities/nearby?lat=${currentUser.location.lat}&lon=${currentUser.location.lon}&maxDistance=5`,
        {
          headers: {
            'X-User-ID': currentUser.userId
          }
        }
      );

      const data = await response.json();

      if (data.success) {
        setActivities(data.data.activities || []);
      } else {
        setError(data.error || 'Failed to load activities');
      }
    } catch (error) {
      setError('Network error. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const getActivityTypeDisplay = (type: string) => {
    switch (type) {
      case 'open_door':
        return 'Open Door';
      case 'public_outing':
        return 'Public Outing';
      case 'private_outing':
        return 'Private Outing';
      default:
        return type;
    }
  };

  const formatDateTime = (dateTimeString: string) => {
    if (!dateTimeString) return null;
    
    try {
      const date = new Date(dateTimeString);
      return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return dateTimeString;
    }
  };

  const filteredActivities = activities.filter(activity => {
    if (filter === 'all') return true;
    return activity.type === filter;
  });

  if (loading) {
    return (
      <div className="card">
        <div className="loading">
          <h3>Loading activities...</h3>
          <p>Finding opportunities in your neighborhood</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <div>
            <h2>Available Activities</h2>
            <p>Connect with families in your area</p>
          </div>
          
          <button className="btn" onClick={fetchActivities}>
            Refresh
          </button>
        </div>

        {/* Filter buttons */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
          <button
            className={`btn ${filter === 'all' ? '' : 'btn-secondary'}`}
            onClick={() => setFilter('all')}
            style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
          >
            All Activities
          </button>
          <button
            className={`btn ${filter === 'open_door' ? '' : 'btn-secondary'}`}
            onClick={() => setFilter('open_door')}
            style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
          >
            Open Door
          </button>
          <button
            className={`btn ${filter === 'public_outing' ? '' : 'btn-secondary'}`}
            onClick={() => setFilter('public_outing')}
            style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
          >
            Public Outings
          </button>
          <button
            className={`btn ${filter === 'private_outing' ? '' : 'btn-secondary'}`}
            onClick={() => setFilter('private_outing')}
            style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
          >
            Private Outings
          </button>
        </div>

        {error && <div className="error">{error}</div>}
      </div>

      {filteredActivities.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', color: '#6c757d' }}>
          <h3>No activities found</h3>
          <p>
            {filter === 'all' 
              ? "There aren't any activities in your area right now." 
              : `No ${getActivityTypeDisplay(filter).toLowerCase()} activities available.`
            }
          </p>
          <p>Be the first to create one!</p>
        </div>
      ) : (
        <div>
          {filteredActivities.map((activity: any) => (
            <div
              key={activity.activityId}
              className="activity-item"
              onClick={() => onActivitySelect?.(activity)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <span className={`activity-type ${activity.type.replace('_', '-')}`}>
                  {getActivityTypeDisplay(activity.type)}
                </span>
                {activity.maxParticipants && (
                  <span style={{ fontSize: '0.875rem', color: '#6c757d' }}>
                    {activity.currentParticipants || 0}/{activity.maxParticipants} spots
                  </span>
                )}
              </div>

              <h3 style={{ marginBottom: '0.5rem', color: '#333' }}>{activity.title}</h3>
              
              {activity.description && (
                <p style={{ marginBottom: '1rem', color: '#666' }}>
                  {activity.description}
                </p>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', fontSize: '0.875rem', color: '#666' }}>
                <div>
                  <strong>Location:</strong> {activity.location}
                </div>
                
                {activity.startTime && (
                  <div>
                    <strong>When:</strong> {formatDateTime(activity.startTime)}
                  </div>
                )}
                
                {activity.creator_name && (
                  <div>
                    <strong>Host:</strong> {activity.creator_name}
                  </div>
                )}
              </div>

              {activity.targetAudience && activity.targetAudience.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  <strong style={{ fontSize: '0.875rem', color: '#666' }}>Perfect for: </strong>
                  <span style={{ fontSize: '0.875rem', color: '#666' }}>
                    {activity.targetAudience.join(', ')}
                  </span>
                </div>
              )}

              <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
                <button className="btn" style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}>
                  Join Activity
                </button>
                <button className="btn btn-secondary" style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}>
                  Message Host
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};