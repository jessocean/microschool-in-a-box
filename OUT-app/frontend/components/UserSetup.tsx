const { useState } = React;

interface UserSetupProps {
  currentUser: any;
  onUserSetupComplete: (user: any) => void;
}

const UserSetup: React.FC<UserSetupProps> = ({ currentUser, onUserSetupComplete }) => {
  const [formData, setFormData] = useState({
    bio: currentUser?.bio || '',
    kidsAges: currentUser?.kidsAges || [],
    socialCircleTypes: currentUser?.socialCircleTypes || [],
    activityPreferences: currentUser?.activityPreferences || [],
    parentingValues: currentUser?.parentingValues || [],
    communicationStyle: currentUser?.communicationStyle || '',
    location: currentUser?.location || { lat: 0, lon: 0, address: '' }
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1);

  const kidsAgeOptions = ['0-2 years', '3-5 years', '6-12 years', '13+ years'];
  const socialCircleOptions = ['Close Friends', 'Neighbors', 'Acquaintances', 'Community'];
  const activityPreferenceOptions = ['Outdoor', 'Indoor', 'Educational', 'Physical', 'Creative', 'Social'];
  const parentingValueOptions = ['Attachment Parenting', 'Positive Discipline', 'Gentle Parenting', 'Montessori', 'Waldorf'];
  const communicationStyleOptions = ['Direct', 'Gentle', 'Collaborative', 'Informal', 'Structured'];

  const handleMultiSelect = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field as keyof typeof prev].includes(value)
        ? (prev[field as keyof typeof prev] as string[]).filter((item: string) => item !== value)
        : [...(prev[field as keyof typeof prev] as string[]), value]
    }));
  };

  const handleLocationChange = (field: string, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      location: {
        ...prev.location,
        [field]: value
      }
    }));
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`/api/users/${currentUser.userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': currentUser.userId
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (data.success) {
        onUserSetupComplete(data.data.user);
      } else {
        setError(data.error || 'Failed to update profile');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStep1 = () => (
    <div>
      <h3>Tell us about yourself</h3>
      
      <div className="form-group">
        <label htmlFor="bio">Bio (Optional)</label>
        <textarea
          id="bio"
          value={formData.bio}
          onChange={(e) => setFormData(prev => ({ ...prev, bio: e.target.value }))}
          placeholder="Share a bit about yourself and your family..."
          rows={3}
        />
      </div>

      <div className="form-group">
        <label>Children's Ages</label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
          {kidsAgeOptions.map(age => (
            <button
              key={age}
              type="button"
              className={`btn ${formData.kidsAges.includes(age) ? '' : 'btn-secondary'}`}
              onClick={() => handleMultiSelect('kidsAges', age)}
              style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
            >
              {age}
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="address">Neighborhood (Optional)</label>
        <input
          type="text"
          id="address"
          value={formData.location.address}
          onChange={(e) => handleLocationChange('address', e.target.value)}
          placeholder="e.g., Brooklyn Heights, Seattle Capitol Hill"
        />
        <small style={{ color: '#6c757d', fontSize: '0.875rem' }}>
          This helps us connect you with nearby families
        </small>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div>
      <h3>How do you like to connect?</h3>
      
      <div className="form-group">
        <label>Social Circle Preferences</label>
        <p style={{ fontSize: '0.875rem', color: '#6c757d', marginBottom: '1rem' }}>
          How do you prefer to build relationships?
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {socialCircleOptions.map(option => (
            <button
              key={option}
              type="button"
              className={`btn ${formData.socialCircleTypes.includes(option) ? '' : 'btn-secondary'}`}
              onClick={() => handleMultiSelect('socialCircleTypes', option)}
              style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Communication Style</label>
        <select
          value={formData.communicationStyle}
          onChange={(e) => setFormData(prev => ({ ...prev, communicationStyle: e.target.value }))}
        >
          <option value="">Select your style...</option>
          {communicationStyleOptions.map(style => (
            <option key={style} value={style}>{style}</option>
          ))}
        </select>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div>
      <h3>Activity preferences</h3>
      
      <div className="form-group">
        <label>Preferred Activities</label>
        <p style={{ fontSize: '0.875rem', color: '#6c757d', marginBottom: '1rem' }}>
          What types of activities interest you?
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {activityPreferenceOptions.map(preference => (
            <button
              key={preference}
              type="button"
              className={`btn ${formData.activityPreferences.includes(preference) ? '' : 'btn-secondary'}`}
              onClick={() => handleMultiSelect('activityPreferences', preference)}
              style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
            >
              {preference}
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Parenting Values (Optional)</label>
        <p style={{ fontSize: '0.875rem', color: '#6c757d', marginBottom: '1rem' }}>
          This helps match you with like-minded families
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {parentingValueOptions.map(value => (
            <button
              key={value}
              type="button"
              className={`btn ${formData.parentingValues.includes(value) ? '' : 'btn-secondary'}`}
              onClick={() => handleMultiSelect('parentingValues', value)}
              style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
            >
              {value}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  const canProceed = () => {
    switch (step) {
      case 1:
        return formData.kidsAges.length > 0;
      case 2:
        return formData.socialCircleTypes.length > 0;
      case 3:
        return formData.activityPreferences.length > 0;
      default:
        return false;
    }
  };

  return (
    <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h2>Complete Your Profile</h2>
        <p>Help us connect you with the right families and activities in your area</p>
        
        {/* Progress indicator */}
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
          {[1, 2, 3].map(stepNum => (
            <div
              key={stepNum}
              style={{
                flex: 1,
                height: '4px',
                backgroundColor: stepNum <= step ? '#667eea' : '#e9ecef',
                borderRadius: '2px'
              }}
            />
          ))}
        </div>
        <p style={{ fontSize: '0.875rem', color: '#6c757d', marginTop: '0.5rem' }}>
          Step {step} of 3
        </p>
      </div>

      {error && <div className="error">{error}</div>}

      {step === 1 && renderStep1()}
      {step === 2 && renderStep2()}
      {step === 3 && renderStep3()}

      <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
        {step > 1 && (
          <button
            className="btn btn-secondary"
            onClick={() => setStep(step - 1)}
            disabled={isLoading}
          >
            Back
          </button>
        )}
        
        {step < 3 ? (
          <button
            className="btn"
            onClick={() => setStep(step + 1)}
            disabled={!canProceed()}
          >
            Next
          </button>
        ) : (
          <button
            className="btn"
            onClick={handleSubmit}
            disabled={!canProceed() || isLoading}
          >
            {isLoading ? 'Saving...' : 'Complete Setup'}
          </button>
        )}
        
        <button
          className="btn btn-secondary"
          onClick={() => onUserSetupComplete(currentUser)}
          disabled={isLoading}
        >
          Skip for Now
        </button>
      </div>
    </div>
  );
};