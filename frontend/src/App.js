import React, { useState, useEffect } from 'react';
import './styles.css';

const API_BASE_URL = process.env.REACT_APP_API_URL;

console.log('API_BASE_URL:', API_BASE_URL)

const Register = ({ onSwitchToLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();
    
    // Validate passwords match
    if (password !== confirmPassword) {
      setError('密碼不匹配');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, username }),
      });

      if (response.ok) {
        setSuccess('註冊成功！請登入您的帳號');
        setError('');
        // Clear form
        setEmail('');
        setPassword('');
        setConfirmPassword('');
        setUsername('');
        
        // Automatically switch to login page after successful registration
        setTimeout(() => {
          onSwitchToLogin();
        }, 2000);
      } else {
        // Clone the response before trying to read its body
        const responseClone = response.clone();
        
        try {
          const errorData = await response.json();
          setError(errorData.message || '註冊失敗，請再試一次');
        } catch (jsonError) {
          // If JSON parsing fails, use the cloned response to get text
          try {
            const errorText = await responseClone.text();
            setError(errorText || '註冊失敗，請再試一次');
          } catch (textError) {
            // If both fail, use status text
            setError(`註冊失敗 (${response.status}: ${response.statusText})`);
          }
        }
      }
    } catch (err) {
      setError('註冊時發生錯誤');
      console.log('Registration error:', err);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2 className="login-title">創建新帳號</h2>
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}
        <form onSubmit={handleRegister}>
          <div className="form-group">
            <label>使用者名稱</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>電子郵件</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>密碼</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>確認密碼</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="login-button">
            註冊
          </button>
        </form>
        <p className="switch-form-text">
          已有帳號？ <button className="text-button" onClick={onSwitchToLogin}>登入</button>
        </p>
      </div>
    </div>
  );
};

const Login = ({ onLoginSuccess, onSwitchToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });
      console.log("api_url", API_BASE_URL);
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        console.log('Login successful:', data);
        onLoginSuccess();
      } else {
        setError('登入失敗，請檢查帳號密碼');
        console.log('Login failed:', response.statusText);
      }
    } catch (err) {
      setError('登入時發生錯誤');
      console.log('Login error:', err);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2 className="login-title">視頻平台登入</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label>電子郵件</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>密碼</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="login-button">
            登入
          </button>
        </form>
        <p className="switch-form-text">
          尚未註冊？ <button className="text-button" onClick={onSwitchToRegister}>創建帳號</button>
        </p>
      </div>
    </div>
  );
};

const VideoUpload = ({ onUploadSuccess }) => {
  const [title, setTitle] = useState('');
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !title) {
      setError('請選擇文件並輸入標題');
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('title', title);
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/videos`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        onUploadSuccess();
      } else {
        setError('上傳失敗');
      }
    } catch (err) {
      setError('上傳時發生錯誤');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="upload-form">
      <h2>上傳新視頻</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>視頻標題</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>視頻文件</label>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setFile(e.target.files[0])}
            required
          />
        </div>
        <button 
          type="submit" 
          className="login-button"
          disabled={isUploading}
        >
          {isUploading ? '上傳中...' : '上傳視頻'}
        </button>
      </form>
    </div>
  );
};

const VideoList = ({ onLogout }) => {
  const [videos, setVideos] = useState([]);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const fetchVideos = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/videos`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setVideos(data);
      }
    } catch (error) {
      console.error('Error fetching videos:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVideoPlay = async (videoId) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${API_BASE_URL}/api/videos/${videoId}/view`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      fetchVideos();
    } catch (error) {
      console.error('Error updating view count:', error);
    }
  };

  const handleDelete = async (videoId) => {
    if (!window.confirm('確定要刪除這個視頻嗎？')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/videos/${videoId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        fetchVideos();
      } else {
        const errorData = await response.json().catch(() => null);
        alert(`刪除失敗: ${errorData?.details || response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting video:', error);
      alert('刪除時發生錯誤: ' + error.message);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, []);

  return (
    <div>
      <div className="navbar">
        <div className="navbar-content">
          <h1>視頻平台</h1>
          <div className="nav-buttons">
            <button 
              onClick={() => setShowUploadForm(!showUploadForm)} 
              className="nav-button primary-button"
            >
              {showUploadForm ? '返回列表' : '上傳視頻'}
            </button>
            <button onClick={onLogout} className="nav-button secondary-button">
              登出
            </button>
          </div>
        </div>
      </div>

      <div className="video-container">
        {showUploadForm ? (
          <VideoUpload 
            onUploadSuccess={() => {
              setShowUploadForm(false);
              fetchVideos();
            }} 
          />
        ) : (
          <div className="video-grid">
            {isLoading ? (
              <div>載入中...</div>
            ) : videos.length === 0 ? (
              <div>暫無視頻</div>
            ) : (
              videos.map(video => (
                <div key={video.id} className="video-card">
                  <video 
                    className="video-thumbnail"
                    controls
                    src={`${API_BASE_URL}/uploads/${video.file_path}`}
                    style={{ width: '100%', height: '200px', objectFit: 'cover' }}
                    onPlay={() => handleVideoPlay(video.id)}
                  />
                  <div className="video-info">
                    <h3 className="video-title">{video.title}</h3>
                    <div className="video-meta">
                      <span>上傳者: {video.uploader}</span>
                      <span>觀看次數: {video.views}</span>
                    </div>
                    <button 
                      onClick={() => handleDelete(video.id)}
                      className="delete-button"
                    >
                      刪除視頻
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const App = () => {
  const [loggedIn, setLoggedIn] = useState(!!localStorage.getItem('token'));
  const [showRegister, setShowRegister] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setLoggedIn(false);
  };

  return (
    <div>
      {loggedIn ? (
        <VideoList onLogout={handleLogout} />
      ) : (
        showRegister ? (
          <Register 
            onSwitchToLogin={() => setShowRegister(false)} 
          />
        ) : (
          <Login 
            onLoginSuccess={() => setLoggedIn(true)} 
            onSwitchToRegister={() => setShowRegister(true)}
          />
        )
      )}
    </div>
  );
};

export default App;