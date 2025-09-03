const { useState } = React;

interface CreateActivityProps {
  currentUser: any;
  onActivityCreated?: (activity: any) => void;
  onCancel?: () => void;
}

const CreateActivity: React.FC<CreateActivityProps> = ({ 
  currentUser, 
  onActivityCreated, 
  onCancel 
}) => {
  const [formData, setFormData] = useState({
    type: 'open_door' as 'open_door' | 'public_outing' | 'private_outing',
    title: '',
    description: '',
    location: '',
    startTime: '',
    endTime: '',
    maxParticipants: '',
    targetAudience: [] as string[]
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const activityTypes = [
    {
      value: 'open_door',
      label: 'Open Door',
      description: 'Welcome families to your home for casual play and connection'
    },
    {
      value: 'public_outing',
      label: 'Public Outing',
      description: 'Organize a meetup at a public location like a park or playground'
    },
    {
      value: 'private_outing',
      label: 'Private Outing',
      description: 'Plan a smaller gathering with specific families you know'
    }
  ];

  const targetAudienceOptions = [
    'Babies (0-12 months)',
    'Toddlers (1-3 years)',
    'Preschoolers (3-5 years)',
    'School age (6-12 years)',
    'Teens (13+ years)',
    'First-time parents',
    'Working parents',
    'Stay-at-home parents',
    'Single parents',
    'Families with special needs'
  ];

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleTargetAudienceToggle = (audience: string) => {
    setFormData(prev => ({
      ...prev,
      targetAudience: prev.targetAudience.includes(audience)
        ? prev.targetAudience.filter(item => item !== audience)
        : [...prev.targetAudience, audience]
    }));
  };

  const validateForm = () => {
    if (!formData.title.trim()) {
      setError('Activity title is required');
      return false;
    }
    if (!formData.location.trim()) {
      setError('Location is required');
      return false;
    }
    if (formData.targetAudience.length === 0) {
      setError('Please select at least one target audience');
      return false;
    }
    if (formData.startTime && formData.endTime) {
      const start = new Date(formData.startTime);
      const end = new Date(formData.endTime);
      if (end <= start) {
        setError('End time must be after start time');
        return false;
      }
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const submitData = {
        ...formData,
        maxParticipants: formData.maxParticipants ? parseInt(formData.maxParticipants) : undefined,
        startTime: formData.startTime || undefined,
        endTime: formData.endTime || undefined
      };

      const response = await fetch('/api/activities', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': currentUser.userId
        },
        body: JSON.stringify(submitData)
      });

      const data = await response.json();

      if (data.success) {
        setSuccess('Activity created successfully!');
        onActivityCreated?.(data.data);
        
        // Reset form
        setFormData({
          type: 'open_door',
          title: '',
          description: '',
          location: '',
          startTime: '',
          endTime: '',
          maxParticipants: '',
          targetAudience: []
        });
      } else {
        setError(data.error || 'Failed to create activity');
      }
    } catch (error) {
      setError('Network error. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getActivityTypeHelp = () => {
    const selectedType = activityTypes.find(type => type.value === formData.type);
    return selectedType?.description || '';
  };

  return (
    <div className="card" style={{ maxWidth: '700px', margin: '0 auto' }}>
      <h2>Create New Activity</h2>
      <p>Share an opportunity with families in your neighborhood</p>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      <form onSubmit={handleSubmit}>
        {/* Activity Type */}
        <div className="form-group">
          <label>Activity Type</label>
          <div style={{ display: 'grid', gap: '0.5rem', marginTop: '0.5rem' }}>
            {activityTypes.map(type => (
              <label
                key={type.value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '1rem',
                  border: `2px solid ${formData.type === type.value ? '#667eea' : '#e9ecef'}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  backgroundColor: formData.type === type.value ? '#f8f9ff' : 'white'
                }}
              >
                <input
                  type="radio"
                  name="activityType"
                  value={type.value}
                  checked={formData.type === type.value}
                  onChange={(e) => handleInputChange('type', e.target.value)}
                  style={{ marginRight: '1rem' }}
                />
                <div>
                  <strong>{type.label}</strong>
                  <div style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.25rem' }}>
                    {type.description}
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Title */}
        <div className="form-group">
          <label htmlFor="title">Activity Title *</label>
          <input
            type="text"
            id="title"
            value={formData.title}
            onChange={(e) => handleInputChange('title', e.target.value)}
            placeholder="e.g., Afternoon Playdate, Park Adventure, Story Time"
            required
          />
        </div>

        {/* Description */}
        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            placeholder="Tell families what to expect, what to bring, or any special details..."
            rows={3}
          />
        </div>

        {/* Location */}
        <div className="form-group">
          <label htmlFor="location">Location *</label>
          <input
            type="text"
            id="location"
            value={formData.location}
            onChange={(e) => handleInputChange('location', e.target.value)}
            placeholder={
              formData.type === 'open_door' 
                ? "Your address or general area" 
                : "Park name, address, or meeting point"
            }
            required
          />
        </div>

        {/* Date and Time */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="form-group">
            <label htmlFor="startTime">Start Time</label>
            <input
              type="datetime-local"
              id="startTime"
              value={formData.startTime}
              onChange={(e) => handleInputChange('startTime', e.target.value)}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="endTime">End Time</label>
            <input
              type="datetime-local"
              id="endTime"
              value={formData.endTime}
              onChange={(e) => handleInputChange('endTime', e.target.value)}
            />
          </div>
        </div>

        {/* Max Participants */}
        <div className="form-group">
          <label htmlFor="maxParticipants">Maximum Participants (Optional)</label>
          <input
            type="number"
            id="maxParticipants"
            value={formData.maxParticipants}
            onChange={(e) => handleInputChange('maxParticipants', e.target.value)}
            placeholder="Leave blank for no limit"
            min="1"
          />
        </div>

        {/* Target Audience */}
        <div className="form-group">
          <label>Who is this perfect for? *</label>
          <p style={{ fontSize: '0.875rem', color: '#6c757d', marginBottom: '1rem' }}>
            Select all that apply to help families find the right activities
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem' }}>
            {targetAudienceOptions.map(audience => (
              <label
                key={audience}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0.5rem',
                  border: `1px solid ${formData.targetAudience.includes(audience) ? '#667eea' : '#e9ecef'}`,
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  backgroundColor: formData.targetAudience.includes(audience) ? '#f8f9ff' : 'white'
                }}
              >
                <input
                  type="checkbox"
                  checked={formData.targetAudience.includes(audience)}
                  onChange={() => handleTargetAudienceToggle(audience)}
                  style={{ marginRight: '0.5rem' }}
                />
                {audience}
              </label>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
          <button
            type="submit"
            className="btn"
            disabled={isLoading}
          >
            {isLoading ? 'Creating Activity...' : 'Create Activity'}
          </button>
          
          {onCancel && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
              disabled={isLoading}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {/* Help text */}
      <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px', fontSize: '0.875rem' }}>
        <strong>Tips for great activities:</strong>
        <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
          <li>Be specific about what families can expect</li>
          <li>Include age-appropriate details</li>
          <li>Mention what to bring or any requirements</li>
          <li>Consider accessibility for all families</li>
        </ul>
      </div>
    </div>
  );
};