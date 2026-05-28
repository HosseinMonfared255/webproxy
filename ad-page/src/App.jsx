import { useState, useEffect } from 'react';
import './App.css';

function App() {
  const INITIAL_TIME = 15;
  
  // Get parameters from URL - now using token instead of direct link
  const params = new URLSearchParams(window.location.search);
  const tokenParam = params.get('token');
  
  // Get file data injected by FastAPI or from window.FILE_DATA
  const fileData = window.FILE_DATA || {};
  
  const [timeLeft, setTimeLeft] = useState(INITIAL_TIME);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isGenerated, setIsGenerated] = useState(false);
  
  // Build download link from token
  const [downloadLink] = useState(tokenParam ? `/stream/${tokenParam}/${encodeURIComponent(fileData.file_name || 'file')}` : '');
  const [fileName] = useState(fileData.file_name || 'فایل ناشناس');
  const [fileSize] = useState(formatFileSize(fileData.file_size || 0));
  const [fileType] = useState(fileData.file_type || 'unknown');

  const dashArray = 377;

  useEffect(() => {
    // Timer countdown
    const timer = setInterval(() => {
      if (document.hidden) return; // Pause timer if tab is not active

      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleGenerate = () => {
    setIsGenerating(true);

    // Open the download link
    setTimeout(() => {
      setIsGenerating(false);
      setIsGenerated(true);
      if (downloadLink) {
        window.open(downloadLink, '_self');
      }
    }, 1200);
  };

  const copyToClipboard = () => {
    if (downloadLink) {
      const fullUrl = `${window.location.origin}${downloadLink}`;
      navigator.clipboard.writeText(fullUrl);
    }
  };

  const offset = dashArray - ((INITIAL_TIME - timeLeft) / INITIAL_TIME) * dashArray;

  return (
    <div className="bg-background text-on-background min-h-screen flex flex-col">
      {/* TopNavBar */}
      <header className="bg-surface-container-lowest dark:bg-inverse-surface border-b border-outline-variant dark:border-outline shadow-sm sticky top-0 z-50">
        <div className="flex flex-row-reverse justify-between items-center w-full px-gutter max-w-container-max mx-auto h-16">
          <div className="font-headline-md text-headline-md font-bold text-primary dark:text-inverse-primary">تک‌دانلود</div>
          <nav className="hidden md:flex flex-row-reverse items-center gap-md">
            <a className="text-primary font-bold border-b-2 border-primary pb-1 font-body-md text-body-md" href="#">صفحه اصلی</a>
            <a className="text-on-surface-variant hover:text-primary transition-colors font-body-md text-body-md" href="#">راهنما</a>
            <a className="text-on-surface-variant hover:text-primary transition-colors font-body-md text-body-md" href="#">قوانین</a>
            <a className="text-on-surface-variant hover:text-primary transition-colors font-body-md text-body-md" href="#">تبلیغات</a>
          </nav>
          <button className="bg-primary text-on-primary px-sm py-xs rounded-lg font-label-md text-label-md transition-all duration-300 hover:bg-primary-container hover:scale-105 active:scale-95 shadow-sm hover:shadow-md">
            ورود / عضویت
          </button>
        </div>
      </header>

      <main className="flex-grow w-full max-w-container-max mx-auto px-gutter py-lg">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-lg items-start">
          {/* Sidebar Ad Left (Desktop) */}
          <aside className="hidden md:block md:col-span-2">
            <div className="ad-placeholder bg-surface border border-outline-variant rounded-md p-sm flex flex-col items-center justify-center min-h-[400px] mb-md cursor-pointer">
              <span className="text-on-surface-variant font-label-md text-label-md mb-xs">محل تبلیغات</span>
              <div className="w-full h-full bg-surface-container flex items-center justify-center opacity-50">
                <span className="material-symbols-outlined text-outline">ads_click</span>
              </div>
            </div>
            <div className="ad-placeholder bg-surface border border-outline-variant rounded-md p-sm flex flex-col items-center justify-center min-h-[400px] cursor-pointer">
              <span className="text-on-surface-variant font-label-md text-label-md mb-xs">محل تبلیغات</span>
              <div className="w-full h-full bg-surface-container flex items-center justify-center opacity-50">
                <span className="material-symbols-outlined text-outline">ads_click</span>
              </div>
            </div>
          </aside>

          {/* Central Content */}
          <section className="md:col-span-8 flex flex-col gap-lg">
            {/* Top Ad Space */}
            <div className="ad-placeholder bg-surface border border-outline-variant rounded-md p-sm text-center h-24 flex items-center justify-center cursor-pointer">
              <span className="text-on-surface-variant font-label-md text-label-md">محل تبلیغات بنری</span>
            </div>

            {/* Main Download Card */}
            <div className="bg-surface-container-lowest rounded-xl download-card-shadow p-xl flex flex-col items-center text-center">
              <div className="mb-md animate-pulse-gentle">
                <span className="material-symbols-outlined text-primary text-[48px]">download_for_offline</span>
              </div>
              <h1 className="font-headline-lg text-headline-lg text-on-surface mb-xs">آماده‌سازی لینک دانلود</h1>
              <p className="text-secondary font-body-md text-body-md mb-lg">فایل شما در حال پردازش نهایی است.</p>

              {/* Timer Section */}
              {timeLeft > 0 && (
                <div className="flex flex-col items-center" id="timer-container">
                  <div className="relative w-32 h-32 flex items-center justify-center mb-md">
                    <svg className="absolute inset-0 w-full h-full -rotate-90">
                      <circle className="text-surface-container" cx="64" cy="64" fill="transparent" r="60" stroke="currentColor" strokeWidth="8"></circle>
                      <circle
                        className="text-primary transition-all duration-1000 ease-linear"
                        cx="64" cy="64" fill="transparent" r="60" stroke="currentColor"
                        strokeDasharray={dashArray} strokeDashoffset={offset} strokeWidth="8">
                      </circle>
                    </svg>
                    <span className="font-timer-display text-timer-display text-primary transition-all duration-300 animate-pulse">
                      {timeLeft.toLocaleString('fa-IR')}
                    </span>
                  </div>
                  <p className="text-on-surface-variant font-body-md text-body-md pulse-animation">لطفاً منتظر بمانید...</p>
                </div>
              )}

              {/* Action Button */}
              {timeLeft === 0 && !isGenerated && (
                <div className="w-full max-w-md" id="action-container">
                  <button
                    disabled={isGenerating || !downloadLink}
                    onClick={handleGenerate}
                    className="w-full bg-primary text-on-primary min-h-[56px] rounded-xl flex items-center justify-center gap-sm font-headline-md text-headline-md transition-all duration-300 hover:bg-primary-container hover:scale-[1.02] active:scale-95 shadow-lg animate-scale-in"
                  >
                    {isGenerating ? (
                      <>
                        <span className="material-symbols-outlined animate-spin">sync</span>
                        <span>در حال ایجاد...</span>
                      </>
                    ) : (
                      <>
                        <span>تولید لینک دانلود</span>
                        <span className="material-symbols-outlined">link</span>
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* Success Message */}
              {isGenerated && (
                <div className="w-full mt-lg p-md bg-secondary-container rounded-lg border border-primary/20 animate-fade-in-up" id="success-container">
                  <div className="flex items-center gap-sm text-on-secondary-container mb-sm">
                    <span className="material-symbols-outlined text-primary success-check-anim" data-weight="fill">verified</span>
                    <span className="font-bold font-body-lg text-body-lg">لینک با موفقیت ایجاد شد</span>
                  </div>
                  <div className="bg-surface-container-lowest p-sm rounded border border-outline-variant flex items-center justify-between group">
                    <code className="text-primary font-body-md text-body-md overflow-hidden text-ellipsis whitespace-nowrap px-2" style={{ direction: 'ltr' }}>
                      {`${window.location.origin}${downloadLink}`}
                    </code>
                    <button onClick={copyToClipboard} className="text-primary hover:bg-primary/10 p-xs rounded transition-all duration-200 active:scale-90" title="کپی کردن لینک">
                      <span className="material-symbols-outlined">content_copy</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* File Info */}
            <div className={`bg-surface-container-low rounded-xl p-md border border-outline-variant transition-all duration-500 ${timeLeft > 0 ? 'shimmer-active' : ''}`}>
              <h3 className="font-headline-md text-headline-md mb-md">مشخصات فایل</h3>
              <div className="space-y-sm">
                <div className="flex justify-between border-b border-outline-variant pb-xs">
                  <span className="text-secondary font-body-md text-body-md">نام فایل:</span>
                  <span className="text-on-surface font-bold font-body-md text-body-md">{fileName}</span>
                </div>
                <div className="flex justify-between border-b border-outline-variant pb-xs">
                  <span className="text-secondary font-body-md text-body-md">حجم:</span>
                  <span className="text-on-surface font-bold font-body-md text-body-md">{fileSize}</span>
                </div>
                <div className="flex justify-between border-b border-outline-variant pb-xs">
                  <span className="text-secondary font-body-md text-body-md">وضعیت:</span>
                  <span className="bg-tertiary-container text-on-tertiary-container px-xs rounded font-label-md text-label-md">تایید شده</span>
                </div>
              </div>
            </div>

            {/* Secondary Banner */}
            <div className="ad-placeholder bg-surface border border-outline-variant rounded-md p-sm text-center h-24 flex items-center justify-center cursor-pointer">
              <span className="text-on-surface-variant font-label-md text-label-md">محل تبلیغات بنری</span>
            </div>

            {/* Bottom Ad Space */}
            <div className="ad-placeholder bg-surface border border-outline-variant rounded-md p-sm text-center h-24 flex items-center justify-center cursor-pointer">
              <span className="text-on-surface-variant font-label-md text-label-md">محل تبلیغات بنری</span>
            </div>
          </section>

          {/* Sidebar Ad Right (Desktop) */}
          <aside className="hidden md:block md:col-span-2">
            <div className="ad-placeholder bg-surface border border-outline-variant rounded-md p-sm flex flex-col items-center justify-center min-h-[400px] mb-md cursor-pointer">
              <span className="text-on-surface-variant font-label-md text-label-md mb-xs">محل تبلیغات</span>
              <div className="w-full h-full bg-surface-container flex items-center justify-center opacity-50">
                <span className="material-symbols-outlined text-outline">ads_click</span>
              </div>
            </div>
            <div className="ad-placeholder bg-surface border border-outline-variant rounded-md p-sm flex flex-col items-center justify-center min-h-[400px] cursor-pointer">
              <span className="text-on-surface-variant font-label-md text-label-md mb-xs">محل تبلیغات</span>
              <div className="w-full h-full bg-surface-container flex items-center justify-center opacity-50">
                <span className="material-symbols-outlined text-outline">ads_click</span>
              </div>
            </div>
          </aside>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-surface-container-low dark:bg-surface-dim border-t border-outline-variant mt-xl">
        <div className="flex flex-col md:flex-row-reverse items-center justify-between px-gutter py-md w-full max-w-container-max mx-auto">
          <div className="font-headline-sm text-headline-sm font-black text-on-surface mb-sm md:mb-0">تک‌دانلود</div>
          <div className="flex gap-md mb-sm md:mb-0">
            <a className="text-on-secondary-fixed-variant hover:text-primary transition-all font-label-md text-label-md" href="#">تماس با ما</a>
            <a className="text-on-secondary-fixed-variant hover:text-primary transition-all font-label-md text-label-md" href="#">درباره ما</a>
            <a className="text-on-secondary-fixed-variant hover:text-primary transition-all font-label-md text-label-md" href="#">حریم خصوصی</a>
            <a className="text-on-secondary-fixed-variant hover:text-primary transition-all font-label-md text-label-md" href="#">سوالات متداول</a>
          </div>
          <p className="text-secondary dark:text-secondary-fixed font-label-md text-label-md opacity-80">© ۲۰۲۴ تمامی حقوق برای تک‌دانلود محفوظ است.</p>
        </div>
      </footer>
    </div>
  );
}

// Helper function to format file size
function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let unitIndex = 0;
  let size = bytes;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`;
}

export default App;
