import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [timeLeft, setTimeLeft] = useState(15)
  const [showDownload, setShowDownload] = useState(false)
  const [downloadLink, setDownloadLink] = useState('')
  const [fileName, setFileName] = useState('')
  const [fileSize, setFileSize] = useState('')

  useEffect(() => {
    // Get parameters from URL
    const params = new URLSearchParams(window.location.search)
    const link = params.get('link') || '#'
    const name = params.get('name') || 'فایل ناشناس'
    const size = params.get('size') || 'نامشخص'
    
    setDownloadLink(link)
    setFileName(name)
    setFileSize(size)

    // Timer countdown
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer)
          setShowDownload(true)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  const handleDownload = () => {
    window.open(downloadLink, '_blank')
  }

  const openAd = (url) => {
    window.open(url, '_blank')
  }

  const progressPercentage = ((15 - timeLeft) / 15) * 100

  return (
    <div className="container">
      <div className="card">
        <h1>📥 دریافت فایل</h1>
        
        <div className="file-info">
          <div className="file-icon">📄</div>
          <div className="file-details">
            <h3>{fileName}</h3>
            <p>حجم: {fileSize}</p>
          </div>
        </div>

        {!showDownload ? (
          <div className="timer-section">
            <div className="timer-display">
              <span className="timer-number">{timeLeft}</span>
              <span className="timer-label">ثانیه تا نمایش لینک دانلود</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progressPercentage}%` }}
              ></div>
            </div>
            <p className="waiting-text">لطفاً صبر کنید...</p>
          </div>
        ) : (
          <div className="download-section">
            <button className="download-btn" onClick={handleDownload}>
              📥 دریافت لینک دانلود
            </button>
            <div className="link-display">
              <p>لینک مستقیم:</p>
              <code>{downloadLink}</code>
            </div>
          </div>
        )}

        <div className="ads-section">
          <h2>📢 تبلیغات</h2>
          <div className="ads-grid">
            <div className="ad-card" onClick={() => openAd('https://example.com/ad1')}>
              <div className="ad-placeholder">تبلیغ ۱</div>
              <p>بهترین خدمات وب</p>
            </div>
            <div className="ad-card" onClick={() => openAd('https://example.com/ad2')}>
              <div className="ad-placeholder">تبلیغ ۲</div>
              <p>خرید آنلاین با تخفیف</p>
            </div>
            <div className="ad-card" onClick={() => openAd('https://example.com/ad3')}>
              <div className="ad-placeholder">تبلیغ ۳</div>
              <p>آموزش برنامه‌نویسی</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
