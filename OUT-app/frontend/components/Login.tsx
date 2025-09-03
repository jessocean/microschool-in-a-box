const { useState } = React;

interface LoginProps {
  onLoginSuccess: (user: any) => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [step, setStep] = useState<'email' | 'sent'>('email');

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (data.success) {
        setMessage('Magic link sent! Check your email and click the link to sign in.');
        setStep('sent');
      } else {
        if (response.status === 404) {
          setError('No account found with this email. Would you like to create an account?');
        } else {
          setError(data.error || 'Failed to send magic link');
        }
      }
    } catch (error) {
      setError('Network error. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateAccount = () => {
    // Redirect to user creation flow
    window.location.href = '/signup';
  };

  if (step === 'sent') {
    return (
      <div className="card" style={{ maxWidth: '500px', margin: '0 auto' }}>
        <h2>Check Your Email</h2>
        <div className="success">
          {message}
        </div>
        <p>
          The magic link will expire in 15 minutes for security. 
          If you don't see the email, check your spam folder.
        </p>
        <button 
          className="btn btn-secondary" 
          onClick={() => setStep('email')}
        >
          Send Another Link
        </button>
      </div>
    );
  }

  return (
    <div className="card" style={{ maxWidth: '500px', margin: '0 auto' }}>
      <h2>Welcome to OUT</h2>
      <p>Connect with families in your neighborhood through shared activities and mutual support.</p>
      
      {error && (
        <div className="error">
          {error}
          {error.includes('No account found') && (
            <button 
              className="btn" 
              onClick={handleCreateAccount}
              style={{ marginTop: '1rem', display: 'block' }}
            >
              Create New Account
            </button>
          )}
        </div>
      )}
      
      <form onSubmit={handleEmailSubmit}>
        <div className="form-group">
          <label htmlFor="email">Email Address</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="Enter your email address"
            disabled={isLoading}
          />
        </div>
        
        <button type="submit" className="btn" disabled={isLoading || !email.trim()}>
          {isLoading ? 'Sending Magic Link...' : 'Send Magic Link'}
        </button>
      </form>
      
      <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <h4>How it works:</h4>
        <ul style={{ margin: '0.5rem 0', paddingLeft: '1.5rem' }}>
          <li>Enter your email address</li>
          <li>We'll send you a secure login link</li>
          <li>Click the link to sign in - no password needed!</li>
        </ul>
        <p style={{ fontSize: '0.875rem', color: '#6c757d', margin: '0.5rem 0 0 0' }}>
          Magic links are more secure than passwords and expire after 15 minutes.
        </p>
      </div>
    </div>
  );
};