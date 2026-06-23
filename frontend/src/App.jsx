import { useState, useCallback } from 'react'
import './index.css'

// ─── Data ───────────────────────────────────────────────────────────────────

const CARS_DATA = [
  {
    id: 1,
    name: 'تويوتا كامري',
    type: 'sedan',
    typeLabel: 'سيدان',
    price: 150,
    seats: 5,
    year: 2024,
    fuel: 'بنزين',
    transmission: 'أوتوماتيك',
    available: true,
    color: '#1a3a6b',
    features: ['بلوتوث', 'كاميرا خلفية', 'تحكم بالمحرك'],
  },
  {
    id: 2,
    name: 'BMW الفئة الخامسة',
    type: 'sedan',
    typeLabel: 'سيدان',
    price: 380,
    seats: 5,
    year: 2024,
    fuel: 'بنزين',
    transmission: 'أوتوماتيك',
    available: true,
    color: '#2a1a4a',
    features: ['شاشة لمس', 'تحكم بالصوت', 'مقاعد جلد', 'نظام ملاحة'],
  },
  {
    id: 3,
    name: 'هيونداي توسان',
    type: 'suv',
    typeLabel: 'دفع رباعي',
    price: 200,
    seats: 5,
    year: 2023,
    fuel: 'بنزين',
    transmission: 'أوتوماتيك',
    available: true,
    color: '#1a4a2a',
    features: ['دفع رباعي', 'فتحة سقف', 'كاميرا 360'],
  },
  {
    id: 4,
    name: 'تويوتا لاند كروزر',
    type: 'suv',
    typeLabel: 'دفع رباعي',
    price: 550,
    seats: 7,
    year: 2024,
    fuel: 'ديزل',
    transmission: 'أوتوماتيك',
    available: false,
    color: '#3a1a1a',
    features: ['7 مقاعد', 'دفع رباعي', 'شاشة 12"', 'مقاعد مدفأة'],
  },
  {
    id: 5,
    name: 'كيا بيكانتو',
    type: 'economy',
    typeLabel: 'اقتصادية',
    price: 80,
    seats: 5,
    year: 2023,
    fuel: 'بنزين',
    transmission: 'أوتوماتيك',
    available: true,
    color: '#1a3a3a',
    features: ['اقتصادي بالوقود', 'سهل القيادة', 'موقف سهل'],
  },
  {
    id: 6,
    name: 'هيونداي إيلانترا',
    type: 'economy',
    typeLabel: 'اقتصادية',
    price: 110,
    seats: 5,
    year: 2024,
    fuel: 'بنزين',
    transmission: 'أوتوماتيك',
    available: true,
    color: '#1a2a4a',
    features: ['بلوتوث', 'شاشة لمس', 'USB'],
  },
]

const INITIAL_BOOKINGS = [
  {
    id: 'BK001',
    name: 'أحمد محمد السعيد',
    phone: '0501234567',
    car: 'تويوتا لاند كروزر',
    days: 3,
    total: 1650,
    status: 'active',
    date: '2026-06-20',
  },
  {
    id: 'BK002',
    name: 'سارة عبدالله الأحمد',
    phone: '0559876543',
    car: 'BMW الفئة الخامسة',
    days: 5,
    total: 1900,
    status: 'pending',
    date: '2026-06-22',
  },
  {
    id: 'BK003',
    name: 'محمد علي الزهراني',
    phone: '0531112233',
    car: 'هيونداي توسان',
    days: 2,
    total: 400,
    status: 'completed',
    date: '2026-06-18',
  },
]

// ─── Icons (inline SVG) ──────────────────────────────────────────────────────

const CarIcon = ({ size = 24, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 17H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v9a2 2 0 0 1-2 2h-2"/>
    <circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>
    <path d="M13 2v5h5"/>
  </svg>
)

const CalendarIcon = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
    <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
    <line x1="3" y1="10" x2="21" y2="10"/>
  </svg>
)

const PhoneIcon = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.58 3.5 2 2 0 0 1 3.55 1.32h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 9.11a16 16 0 0 0 6 6l1.36-1.36a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
  </svg>
)

const UserIcon = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)

const CloseIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
)

const CheckIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)

const StarIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="#d4a017" stroke="#d4a017" strokeWidth="1">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
  </svg>
)

// ─── Car SVG Illustration ────────────────────────────────────────────────────

const CarIllustration = ({ color = '#1a3a6b', type = 'sedan' }) => {
  if (type === 'suv') {
    return (
      <svg viewBox="0 0 200 100" width="160" height="80" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id={`suv-${color}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{stopColor: color, stopOpacity: 1}} />
            <stop offset="100%" style={{stopColor: '#0a0f1e', stopOpacity: 1}} />
          </linearGradient>
          <linearGradient id={`roof-${color}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style={{stopColor: '#d4a017', stopOpacity: 0.3}} />
            <stop offset="100%" style={{stopColor: color, stopOpacity: 1}} />
          </linearGradient>
        </defs>
        <rect x="20" y="30" width="160" height="45" rx="8" fill={`url(#suv-${color})`}/>
        <rect x="30" y="15" width="130" height="30" rx="6" fill={`url(#roof-${color})`}/>
        <rect x="35" y="18" width="50" height="22" rx="4" fill="rgba(120,200,255,0.3)" stroke="rgba(120,200,255,0.5)" strokeWidth="1"/>
        <rect x="95" y="18" width="55" height="22" rx="4" fill="rgba(120,200,255,0.3)" stroke="rgba(120,200,255,0.5)" strokeWidth="1"/>
        <circle cx="55" cy="78" r="14" fill="#0a0f1e" stroke="#d4a017" strokeWidth="2"/>
        <circle cx="55" cy="78" r="8" fill="#1a2744" stroke="#d4a017" strokeWidth="1"/>
        <circle cx="145" cy="78" r="14" fill="#0a0f1e" stroke="#d4a017" strokeWidth="2"/>
        <circle cx="145" cy="78" r="8" fill="#1a2744" stroke="#d4a017" strokeWidth="1"/>
        <rect x="20" y="42" width="12" height="8" rx="2" fill="#f0c040"/>
        <rect x="168" y="42" width="12" height="8" rx="2" fill="rgba(255,50,50,0.8)"/>
        <rect x="22" y="55" width="4" height="15" rx="2" fill="#d4a017" opacity="0.5"/>
      </svg>
    )
  }
  if (type === 'economy') {
    return (
      <svg viewBox="0 0 200 100" width="160" height="80" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id={`eco-${color}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{stopColor: color, stopOpacity: 1}} />
            <stop offset="100%" style={{stopColor: '#0a0f1e', stopOpacity: 1}} />
          </linearGradient>
        </defs>
        <rect x="25" y="40" width="150" height="38" rx="6" fill={`url(#eco-${color})`}/>
        <path d="M60 40 Q80 20 120 20 Q150 20 160 40" fill={`url(#eco-${color})`} stroke="none"/>
        <rect x="65" y="22" width="40" height="20" rx="4" fill="rgba(120,200,255,0.3)" stroke="rgba(120,200,255,0.5)" strokeWidth="1"/>
        <rect x="110" y="22" width="40" height="20" rx="4" fill="rgba(120,200,255,0.3)" stroke="rgba(120,200,255,0.5)" strokeWidth="1"/>
        <circle cx="60" cy="78" r="13" fill="#0a0f1e" stroke="#d4a017" strokeWidth="2"/>
        <circle cx="60" cy="78" r="7" fill="#1a2744"/>
        <circle cx="140" cy="78" r="13" fill="#0a0f1e" stroke="#d4a017" strokeWidth="2"/>
        <circle cx="140" cy="78" r="7" fill="#1a2744"/>
        <rect x="25" y="48" width="10" height="7" rx="2" fill="#f0c040"/>
        <rect x="165" y="48" width="10" height="7" rx="2" fill="rgba(255,50,50,0.8)"/>
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 200 100" width="160" height="80" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id={`sedan-${color}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{stopColor: color, stopOpacity: 1}} />
          <stop offset="100%" style={{stopColor: '#0a0f1e', stopOpacity: 1}} />
        </linearGradient>
        <linearGradient id={`top-${color}`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" style={{stopColor: '#d4a017', stopOpacity: 0.2}} />
          <stop offset="100%" style={{stopColor: color, stopOpacity: 1}} />
        </linearGradient>
      </defs>
      <rect x="15" y="38" width="170" height="40" rx="8" fill={`url(#sedan-${color})`}/>
      <path d="M50 38 Q75 18 125 18 Q155 18 165 38" fill={`url(#top-${color})`}/>
      <rect x="58" y="20" width="42" height="20" rx="3" fill="rgba(120,200,255,0.35)" stroke="rgba(120,200,255,0.6)" strokeWidth="1"/>
      <rect x="105" y="20" width="48" height="20" rx="3" fill="rgba(120,200,255,0.35)" stroke="rgba(120,200,255,0.6)" strokeWidth="1"/>
      <circle cx="52" cy="78" r="14" fill="#0a0f1e" stroke="#d4a017" strokeWidth="2.5"/>
      <circle cx="52" cy="78" r="8" fill="#1a2744" stroke="#d4a017" strokeWidth="1"/>
      <circle cx="148" cy="78" r="14" fill="#0a0f1e" stroke="#d4a017" strokeWidth="2.5"/>
      <circle cx="148" cy="78" r="8" fill="#1a2744" stroke="#d4a017" strokeWidth="1"/>
      <rect x="15" y="46" width="14" height="9" rx="3" fill="#f0c040" opacity="0.9"/>
      <rect x="171" y="46" width="14" height="9" rx="3" fill="rgba(255,50,50,0.9)"/>
      <line x1="15" y1="60" x2="185" y2="60" stroke="rgba(212,160,23,0.15)" strokeWidth="1"/>
    </svg>
  )
}

// ─── Navbar ──────────────────────────────────────────────────────────────────

function Navbar({ currentPage, setCurrentPage }) {
  const [mobileOpen, setMobileOpen] = useState(false)

  const links = [
    { id: 'home', label: 'الرئيسية' },
    { id: 'cars', label: 'معرض السيارات' },
    { id: 'about', label: 'عن المكتب' },
    { id: 'contact', label: 'تواصل معنا' },
  ]

  return (
    <nav style={{
      background: 'rgba(6, 13, 31, 0.95)',
      borderBottom: '1px solid rgba(212, 160, 23, 0.2)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <div style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: '0 24px',
        height: 72,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        {/* Logo */}
        <div
          style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}
          onClick={() => setCurrentPage('home')}
        >
          <div style={{
            width: 42, height: 42,
            background: 'linear-gradient(135deg, #d4a017, #f0c040)',
            borderRadius: 10,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <CarIcon size={22} color="#060d1f" />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 18, color: '#fff', letterSpacing: 0.5 }}>
              الهدى
            </div>
            <div style={{ fontSize: 11, color: '#d4a017', letterSpacing: 1 }}>لتأجير السيارات</div>
          </div>
        </div>

        {/* Desktop Nav */}
        <div style={{ display: 'flex', gap: 32, alignItems: 'center' }}>
          {links.map(l => (
            <span
              key={l.id}
              className="nav-link"
              style={{ fontWeight: currentPage === l.id ? 600 : 400 }}
              onClick={() => setCurrentPage(l.id)}
            >
              {l.label}
            </span>
          ))}
          <button
            className="gold-btn"
            style={{ padding: '8px 20px', borderRadius: 8, fontSize: 14 }}
            onClick={() => setCurrentPage('dashboard')}
          >
            لوحة التحكم
          </button>
        </div>
      </div>
    </nav>
  )
}

// ─── Hero Section ────────────────────────────────────────────────────────────

function HeroSection({ onSearch, setCurrentPage }) {
  const today = new Date().toISOString().split('T')[0]
  const [form, setForm] = useState({
    pickup: today,
    dropoff: '',
    carType: 'all',
  })

  const handleSearch = (e) => {
    e.preventDefault()
    onSearch(form)
    setCurrentPage('cars')
  }

  return (
    <section className="hero-bg" style={{ minHeight: '88vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '60px 24px' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto', width: '100%', position: 'relative', zIndex: 1 }}>
        {/* Badge */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
          <span style={{
            background: 'rgba(212, 160, 23, 0.1)',
            border: '1px solid rgba(212, 160, 23, 0.4)',
            color: '#d4a017',
            padding: '6px 20px',
            borderRadius: 20,
            fontSize: 13,
            fontWeight: 600,
            letterSpacing: 1,
          }}>
            ✦ مكتب الهدى لتأجير السيارات ✦
          </span>
        </div>

        {/* Headline */}
        <h1 style={{
          textAlign: 'center',
          fontSize: 'clamp(36px, 6vw, 72px)',
          fontWeight: 900,
          lineHeight: 1.15,
          margin: '0 0 16px',
          color: '#fff',
        }}>
          تجربة قيادة{' '}
          <span style={{ background: 'linear-gradient(135deg, #d4a017, #f0c040)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
            استثنائية
          </span>
        </h1>
        <p style={{
          textAlign: 'center',
          fontSize: 'clamp(16px, 2vw, 20px)',
          color: '#9ca3af',
          margin: '0 0 48px',
          lineHeight: 1.7,
        }}>
          أفضل سيارات الفئة الأولى بأسعار تنافسية · خدمة 24/7 · تأمين شامل
        </p>

        {/* Search Card */}
        <form onSubmit={handleSearch}>
          <div style={{
            background: 'rgba(13, 31, 60, 0.9)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(212, 160, 23, 0.3)',
            borderRadius: 20,
            padding: 'clamp(20px, 4vw, 36px)',
            boxShadow: '0 24px 80px rgba(0,0,0,0.4)',
          }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 20,
              marginBottom: 24,
            }}>
              <div>
                <label style={{ display: 'block', color: '#d4a017', fontSize: 13, fontWeight: 600, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <CalendarIcon size={14} /> تاريخ الاستلام
                </label>
                <input
                  type="date"
                  value={form.pickup}
                  min={today}
                  onChange={e => setForm(f => ({ ...f, pickup: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', color: '#d4a017', fontSize: 13, fontWeight: 600, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <CalendarIcon size={14} /> تاريخ التسليم
                </label>
                <input
                  type="date"
                  value={form.dropoff}
                  min={form.pickup || today}
                  onChange={e => setForm(f => ({ ...f, dropoff: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', color: '#d4a017', fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
                  نوع السيارة
                </label>
                <select
                  value={form.carType}
                  onChange={e => setForm(f => ({ ...f, carType: e.target.value }))}
                >
                  <option value="all">جميع الأنواع</option>
                  <option value="sedan">سيدان</option>
                  <option value="suv">دفع رباعي</option>
                  <option value="economy">اقتصادية</option>
                </select>
              </div>
            </div>
            <button type="submit" className="gold-btn" style={{
              width: '100%',
              padding: '14px',
              borderRadius: 12,
              fontSize: 17,
              letterSpacing: 0.5,
            }}>
              ابحث عن سيارتك المثالية ←
            </button>
          </div>
        </form>

        {/* Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 20,
          marginTop: 48,
          maxWidth: 600,
          margin: '48px auto 0',
        }}>
          {[
            { label: 'سيارة متاحة', value: '15+' },
            { label: 'عميل راضٍ', value: '500+' },
            { label: 'سنوات خبرة', value: '8+' },
          ].map((s, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 'clamp(28px, 4vw, 40px)', fontWeight: 900, color: '#d4a017' }}>{s.value}</div>
              <div style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── Car Gallery ─────────────────────────────────────────────────────────────

function CarGallery({ searchFilter, onBookCar }) {
  const [activeFilter, setActiveFilter] = useState(searchFilter?.carType || 'all')

  const filtered = CARS_DATA.filter(c => activeFilter === 'all' || c.type === activeFilter)

  const filters = [
    { key: 'all', label: 'الكل' },
    { key: 'sedan', label: 'سيدان' },
    { key: 'suv', label: 'دفع رباعي SUV' },
    { key: 'economy', label: 'اقتصادية' },
  ]

  return (
    <section style={{ padding: '80px 24px', maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <span style={{ color: '#d4a017', fontSize: 13, fontWeight: 600, letterSpacing: 2, textTransform: 'uppercase' }}>
          أسطولنا
        </span>
        <h2 style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 800, margin: '12px 0 16px', color: '#fff' }}>
          اختر سيارتك المثالية
        </h2>
        <p style={{ color: '#6b7280', fontSize: 16, maxWidth: 500, margin: '0 auto' }}>
          مجموعة متنوعة من أرقى السيارات لتلبية جميع احتياجاتك
        </p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginBottom: 40, flexWrap: 'wrap' }}>
        {filters.map(f => (
          <button
            key={f.key}
            className={`filter-btn ${activeFilter === f.key ? 'active' : ''}`}
            onClick={() => setActiveFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: 24,
      }}>
        {filtered.map((car, idx) => (
          <div key={car.id} className="car-card animate-fade-in" style={{ animationDelay: `${idx * 0.1}s` }}>
            {/* Image area */}
            <div style={{
              background: `linear-gradient(135deg, ${car.color}33 0%, #060d1f 100%)`,
              padding: '28px 20px 16px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              position: 'relative',
            }}>
              <div style={{ position: 'absolute', top: 16, right: 16 }}>
                <span className={car.available ? 'badge-available' : 'badge-rented'}>
                  {car.available ? '● متاحة' : '● مؤجرة'}
                </span>
              </div>
              <div style={{ position: 'absolute', top: 16, left: 16, background: 'rgba(212,160,23,0.1)', border: '1px solid rgba(212,160,23,0.3)', borderRadius: 6, padding: '2px 10px', fontSize: 12, color: '#d4a017' }}>
                {car.typeLabel}
              </div>
              <CarIllustration color={car.color} type={car.type} />
              <div style={{ display: 'flex', gap: 2, marginTop: 8 }}>
                {[1,2,3,4,5].map(s => <StarIcon key={s} />)}
              </div>
            </div>

            {/* Details */}
            <div style={{ padding: '20px 20px 24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#fff' }}>{car.name}</h3>
                  <span style={{ fontSize: 13, color: '#6b7280' }}>{car.year} · {car.fuel} · {car.transmission}</span>
                </div>
                <div style={{ textAlign: 'left' }}>
                  <span style={{ fontSize: 24, fontWeight: 900, color: '#d4a017' }}>{car.price}</span>
                  <span style={{ fontSize: 12, color: '#6b7280' }}> ر.س/يوم</span>
                </div>
              </div>

              {/* Specs row */}
              <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
                {[
                  { icon: '👤', label: `${car.seats} مقاعد` },
                  { icon: '⚙️', label: car.transmission },
                  { icon: '⛽', label: car.fuel },
                ].map((spec, i) => (
                  <span key={i} style={{ fontSize: 12, color: '#9ca3af' }}>{spec.icon} {spec.label}</span>
                ))}
              </div>

              {/* Features */}
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
                {car.features.slice(0, 3).map((f, i) => (
                  <span key={i} style={{
                    fontSize: 11, padding: '3px 10px', borderRadius: 12,
                    background: 'rgba(212,160,23,0.08)', color: '#d4a017',
                    border: '1px solid rgba(212,160,23,0.2)',
                  }}>
                    {f}
                  </span>
                ))}
              </div>

              <button
                className="gold-btn"
                style={{
                  width: '100%', padding: '12px', borderRadius: 10, fontSize: 15,
                  opacity: car.available ? 1 : 0.5,
                  cursor: car.available ? 'pointer' : 'not-allowed',
                }}
                disabled={!car.available}
                onClick={() => car.available && onBookCar(car)}
              >
                {car.available ? '🔑 احجز الآن' : '⏳ غير متاحة حالياً'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

// ─── Booking Modal ───────────────────────────────────────────────────────────

function BookingModal({ car, onClose, onConfirm }) {
  const today = new Date().toISOString().split('T')[0]
  const [step, setStep] = useState(1)
  const [form, setForm] = useState({
    name: '', phone: '', idNumber: '', licenseNumber: '',
    pickup: today, dropoff: '',
  })
  const [submitted, setSubmitted] = useState(false)

  const days = form.pickup && form.dropoff
    ? Math.max(1, Math.ceil((new Date(form.dropoff) - new Date(form.pickup)) / 86400000))
    : 1
  const total = car.price * days

  const handleSubmit = (e) => {
    e.preventDefault()
    onConfirm({ ...form, car, days, total })
    setSubmitted(true)
  }

  if (submitted) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={e => e.stopPropagation()} style={{ textAlign: 'center' }}>
          <div style={{
            width: 72, height: 72,
            background: 'linear-gradient(135deg, #22c55e, #16a34a)',
            borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 20px',
          }}>
            <CheckIcon />
          </div>
          <h2 style={{ color: '#fff', fontSize: 24, fontWeight: 800, marginBottom: 8 }}>تم الحجز بنجاح! 🎉</h2>
          <p style={{ color: '#9ca3af', lineHeight: 1.7, marginBottom: 24 }}>
            سيتصل بك فريقنا خلال دقائق لتأكيد الحجز وترتيب الاستلام.
          </p>
          <div style={{
            background: 'rgba(212,160,23,0.08)',
            border: '1px solid rgba(212,160,23,0.2)',
            borderRadius: 12, padding: 20, marginBottom: 24, textAlign: 'right',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ color: '#6b7280' }}>السيارة</span>
              <span style={{ color: '#fff', fontWeight: 600 }}>{car.name}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ color: '#6b7280' }}>عدد الأيام</span>
              <span style={{ color: '#fff', fontWeight: 600 }}>{days} يوم</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid rgba(212,160,23,0.2)', paddingTop: 12 }}>
              <span style={{ color: '#d4a017', fontWeight: 700 }}>الإجمالي</span>
              <span style={{ color: '#d4a017', fontWeight: 900, fontSize: 20 }}>{total} ر.س</span>
            </div>
          </div>
          <button className="gold-btn" style={{ padding: '12px 32px', borderRadius: 10, fontSize: 15 }} onClick={onClose}>
            حسناً، شكراً!
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content scrollbar-gold" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#fff' }}>استمارة الحجز</h2>
            <p style={{ margin: '4px 0 0', color: '#d4a017', fontSize: 14 }}>{car.name}</p>
          </div>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: 8, cursor: 'pointer', color: '#9ca3af' }}>
            <CloseIcon />
          </button>
        </div>

        {/* Progress */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 28 }}>
          {[1, 2].map(s => (
            <div key={s} style={{
              flex: 1, height: 4, borderRadius: 2,
              background: step >= s ? 'linear-gradient(90deg, #d4a017, #f0c040)' : 'rgba(255,255,255,0.1)',
              transition: 'background 0.3s',
            }} />
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          {step === 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <h3 style={{ margin: '0 0 8px', color: '#d4a017', fontSize: 15, fontWeight: 600 }}>
                1️⃣ بيانات المستأجر
              </h3>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 6 }}>الاسم الكامل *</label>
                <input
                  type="text"
                  placeholder="أحمد محمد السعيد"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 6 }}>رقم الجوال *</label>
                <input
                  type="tel"
                  placeholder="05XXXXXXXX"
                  value={form.phone}
                  onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 6 }}>رقم الهوية / الإقامة *</label>
                <input
                  type="text"
                  placeholder="XXXXXXXXXX"
                  value={form.idNumber}
                  onChange={e => setForm(f => ({ ...f, idNumber: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 6 }}>رقم رخصة القيادة *</label>
                <input
                  type="text"
                  placeholder="XXXXXXXXX"
                  value={form.licenseNumber}
                  onChange={e => setForm(f => ({ ...f, licenseNumber: e.target.value }))}
                  required
                />
              </div>
              <button
                type="button"
                className="gold-btn"
                style={{ padding: '13px', borderRadius: 10, fontSize: 15, marginTop: 8 }}
                onClick={() => {
                  if (form.name && form.phone && form.idNumber && form.licenseNumber) setStep(2)
                }}
              >
                التالي: تفاصيل الحجز ←
              </button>
            </div>
          )}

          {step === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <h3 style={{ margin: '0 0 8px', color: '#d4a017', fontSize: 15, fontWeight: 600 }}>
                2️⃣ تفاصيل الحجز
              </h3>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 6 }}>تاريخ الاستلام *</label>
                <input
                  type="date"
                  value={form.pickup}
                  min={today}
                  onChange={e => setForm(f => ({ ...f, pickup: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 6 }}>تاريخ التسليم *</label>
                <input
                  type="date"
                  value={form.dropoff}
                  min={form.pickup || today}
                  onChange={e => setForm(f => ({ ...f, dropoff: e.target.value }))}
                  required
                />
              </div>

              {/* Price breakdown */}
              {form.dropoff && (
                <div style={{
                  background: 'rgba(212,160,23,0.06)',
                  border: '1px solid rgba(212,160,23,0.2)',
                  borderRadius: 12,
                  padding: 20,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                    <span style={{ color: '#9ca3af', fontSize: 14 }}>سعر اليوم</span>
                    <span style={{ color: '#fff' }}>{car.price} ر.س</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                    <span style={{ color: '#9ca3af', fontSize: 14 }}>عدد الأيام</span>
                    <span style={{ color: '#fff' }}>{days} يوم</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                    <span style={{ color: '#9ca3af', fontSize: 14 }}>التأمين الشامل</span>
                    <span style={{ color: '#4ade80', fontSize: 13 }}>مشمول ✓</span>
                  </div>
                  <div style={{
                    borderTop: '1px solid rgba(212,160,23,0.2)',
                    paddingTop: 12,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}>
                    <span style={{ color: '#d4a017', fontWeight: 700, fontSize: 15 }}>الإجمالي</span>
                    <span style={{ color: '#d4a017', fontWeight: 900, fontSize: 26 }}>{total} <span style={{ fontSize: 14 }}>ر.س</span></span>
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', gap: 12 }}>
                <button type="button" onClick={() => setStep(1)} style={{
                  flex: 1, padding: '12px', borderRadius: 10, fontSize: 14,
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: '#9ca3af', cursor: 'pointer',
                }}>
                  → رجوع
                </button>
                <button type="submit" className="gold-btn" style={{ flex: 2, padding: '13px', borderRadius: 10, fontSize: 15 }}>
                  ✅ تأكيد الحجز
                </button>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}

// ─── Dashboard ───────────────────────────────────────────────────────────────

function Dashboard({ bookings }) {
  const [activeTab, setActiveTab] = useState('overview')

  const allBookings = [...INITIAL_BOOKINGS, ...bookings]
  const activeCount = allBookings.filter(b => b.status === 'active').length
  const pendingCount = allBookings.filter(b => b.status === 'pending').length
  const totalRevenue = allBookings.reduce((sum, b) => sum + (b.total || 0), 0)
  const rentedCars = CARS_DATA.filter(c => !c.available).length

  const tabs = [
    { id: 'overview', icon: '📊', label: 'نظرة عامة' },
    { id: 'bookings', icon: '📋', label: 'الطلبات' },
    { id: 'fleet', icon: '🚗', label: 'الأسطول' },
  ]

  const statusMap = {
    active: { label: 'نشط', color: '#4ade80', bg: 'rgba(74,222,128,0.1)' },
    pending: { label: 'معلق', color: '#fbbf24', bg: 'rgba(251,191,36,0.1)' },
    completed: { label: 'مكتمل', color: '#60a5fa', bg: 'rgba(96,165,250,0.1)' },
  }

  return (
    <section style={{ padding: '40px 24px', maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 36 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 28, fontWeight: 800, color: '#fff' }}>لوحة تحكم المكتب</h2>
          <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: 14 }}>
            آخر تحديث: {new Date().toLocaleDateString('ar-SA', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <div style={{
          background: 'rgba(212,160,23,0.1)',
          border: '1px solid rgba(212,160,23,0.3)',
          borderRadius: 10,
          padding: '8px 16px',
          color: '#d4a017',
          fontSize: 13,
          fontWeight: 600,
        }}>
          🔒 صاحب المكتب
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, background: 'rgba(13,31,60,0.6)', borderRadius: 12, padding: 4, marginBottom: 32, width: 'fit-content' }}>
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            style={{
              padding: '10px 20px',
              borderRadius: 10,
              border: 'none',
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: activeTab === t.id ? 700 : 400,
              background: activeTab === t.id ? 'linear-gradient(135deg, #d4a017, #f0c040)' : 'transparent',
              color: activeTab === t.id ? '#060d1f' : '#9ca3af',
              transition: 'all 0.3s',
            }}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Overview */}
      {activeTab === 'overview' && (
        <>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 20,
            marginBottom: 36,
          }}>
            {[
              { icon: '🚗', label: 'إجمالي السيارات', value: CARS_DATA.length, color: '#60a5fa' },
              { icon: '🔑', label: 'مؤجرة حالياً', value: rentedCars, color: '#f87171' },
              { icon: '✅', label: 'متاحة', value: CARS_DATA.length - rentedCars, color: '#4ade80' },
              { icon: '⏳', label: 'طلبات معلقة', value: pendingCount, color: '#fbbf24' },
              { icon: '💰', label: 'إجمالي الإيرادات', value: `${totalRevenue.toLocaleString()} ر.س`, color: '#d4a017' },
              { icon: '📋', label: 'إجمالي الطلبات', value: allBookings.length, color: '#a78bfa' },
            ].map((stat, i) => (
              <div key={i} className="stat-card">
                <div style={{ fontSize: 28, marginBottom: 12 }}>{stat.icon}</div>
                <div style={{ fontSize: 'clamp(20px, 3vw, 30px)', fontWeight: 900, color: stat.color, marginBottom: 6 }}>
                  {stat.value}
                </div>
                <div style={{ fontSize: 13, color: '#6b7280' }}>{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Recent bookings preview */}
          <div style={{
            background: 'rgba(13,31,60,0.6)',
            border: '1px solid rgba(212,160,23,0.15)',
            borderRadius: 16,
            overflow: 'hidden',
          }}>
            <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(212,160,23,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#fff' }}>آخر الطلبات</h3>
              {pendingCount > 0 && (
                <span style={{ background: 'rgba(251,191,36,0.15)', color: '#fbbf24', padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600, border: '1px solid rgba(251,191,36,0.3)' }}>
                  {pendingCount} طلب جديد
                </span>
              )}
            </div>
            {allBookings.slice(-3).reverse().map((b, i) => (
              <div key={i} style={{
                padding: '16px 24px',
                borderBottom: '1px solid rgba(255,255,255,0.04)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 12,
              }}>
                <div>
                  <div style={{ fontWeight: 600, color: '#fff', fontSize: 15 }}>{b.name}</div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{b.car} · {b.phone}</div>
                </div>
                <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                  <span style={{ fontWeight: 700, color: '#d4a017' }}>{(b.total || 0).toLocaleString()} ر.س</span>
                  <span style={{
                    padding: '4px 14px',
                    borderRadius: 20,
                    fontSize: 12,
                    fontWeight: 600,
                    background: statusMap[b.status]?.bg,
                    color: statusMap[b.status]?.color,
                  }}>
                    {statusMap[b.status]?.label}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Bookings tab */}
      {activeTab === 'bookings' && (
        <div style={{
          background: 'rgba(13,31,60,0.6)',
          border: '1px solid rgba(212,160,23,0.15)',
          borderRadius: 16,
          overflow: 'hidden',
        }}>
          <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(212,160,23,0.1)' }}>
            <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#fff' }}>جميع طلبات الحجز ({allBookings.length})</h3>
          </div>
          {allBookings.length === 0 ? (
            <div style={{ padding: 48, textAlign: 'center', color: '#6b7280' }}>لا توجد طلبات بعد</div>
          ) : (
            allBookings.map((b, i) => (
              <div key={i} style={{
                padding: '18px 24px',
                borderBottom: '1px solid rgba(255,255,255,0.04)',
                display: 'grid',
                gridTemplateColumns: '1fr 1fr auto auto',
                gap: 16,
                alignItems: 'center',
              }}>
                <div>
                  <div style={{ fontWeight: 600, color: '#fff' }}>{b.name}</div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>
                    <PhoneIcon size={11} /> {b.phone}
                  </div>
                </div>
                <div>
                  <div style={{ color: '#e2e8f0', fontSize: 14 }}>{b.car}</div>
                  <div style={{ fontSize: 12, color: '#6b7280' }}>{b.days || '?'} يوم · {b.date}</div>
                </div>
                <div style={{ fontWeight: 800, color: '#d4a017', fontSize: 16 }}>{(b.total || 0).toLocaleString()} ر.س</div>
                <span style={{
                  padding: '5px 14px',
                  borderRadius: 20,
                  fontSize: 12,
                  fontWeight: 600,
                  background: statusMap[b.status]?.bg,
                  color: statusMap[b.status]?.color,
                  whiteSpace: 'nowrap',
                }}>
                  {statusMap[b.status]?.label}
                </span>
              </div>
            ))
          )}
        </div>
      )}

      {/* Fleet tab */}
      {activeTab === 'fleet' && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: 20,
        }}>
          {CARS_DATA.map((car) => (
            <div key={car.id} style={{
              background: 'rgba(13,31,60,0.7)',
              border: `1px solid ${car.available ? 'rgba(74,222,128,0.2)' : 'rgba(248,113,113,0.2)'}`,
              borderRadius: 16,
              padding: 20,
              display: 'flex',
              gap: 16,
              alignItems: 'center',
            }}>
              <div style={{ background: `${car.color}22`, borderRadius: 10, padding: 10 }}>
                <CarIllustration color={car.color} type={car.type} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, color: '#fff', fontSize: 15 }}>{car.name}</div>
                <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>{car.typeLabel} · {car.year}</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#d4a017', fontWeight: 700 }}>{car.price} ر.س/يوم</span>
                  <span className={car.available ? 'badge-available' : 'badge-rented'}>
                    {car.available ? 'متاحة' : 'مؤجرة'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

// ─── About Page ───────────────────────────────────────────────────────────────

function AboutPage() {
  return (
    <section style={{ padding: '80px 24px', maxWidth: 900, margin: '0 auto', textAlign: 'center' }}>
      <span style={{ color: '#d4a017', fontSize: 13, fontWeight: 600, letterSpacing: 2 }}>من نحن</span>
      <h2 style={{ fontSize: 40, fontWeight: 900, margin: '16px 0 20px', color: '#fff' }}>مكتب الهدى لتأجير السيارات</h2>
      <p style={{ color: '#9ca3af', fontSize: 17, lineHeight: 1.8, marginBottom: 48 }}>
        نحن مكتب متخصص في تأجير السيارات الفاخرة والاقتصادية، نخدم عملاءنا منذ أكثر من 8 سنوات بأعلى معايير الجودة والأمان. أسطولنا يضم أحدث موديلات السيارات مع تأمين شامل وخدمة عملاء على مدار الساعة.
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 24 }}>
        {[
          { icon: '🛡️', title: 'تأمين شامل', desc: 'جميع سياراتنا مؤمنة تأميناً شاملاً' },
          { icon: '🕐', title: 'خدمة 24/7', desc: 'فريق دعم متاح على مدار الساعة' },
          { icon: '🚗', title: 'أسطول متنوع', desc: 'أكثر من 15 سيارة بمختلف الفئات' },
          { icon: '💎', title: 'جودة مضمونة', desc: 'سيارات نظيفة ومصانة دورياً' },
        ].map((item, i) => (
          <div key={i} className="glass-card" style={{ borderRadius: 16, padding: 28 }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>{item.icon}</div>
            <div style={{ fontWeight: 700, color: '#fff', marginBottom: 8 }}>{item.title}</div>
            <div style={{ color: '#6b7280', fontSize: 14 }}>{item.desc}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

// ─── Contact Page ─────────────────────────────────────────────────────────────

function ContactPage() {
  const [sent, setSent] = useState(false)
  const [form, setForm] = useState({ name: '', phone: '', message: '' })

  return (
    <section style={{ padding: '80px 24px', maxWidth: 700, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <span style={{ color: '#d4a017', fontSize: 13, fontWeight: 600, letterSpacing: 2 }}>تواصل معنا</span>
        <h2 style={{ fontSize: 40, fontWeight: 900, margin: '16px 0 16px', color: '#fff' }}>نحن هنا لمساعدتك</h2>
        <p style={{ color: '#9ca3af' }}>للاستفسار أو الحجز المسبق، تواصل معنا عبر القنوات التالية</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 40 }}>
        {[
          { icon: '📞', label: 'الهاتف', value: '0501234567' },
          { icon: '💬', label: 'واتساب', value: '0501234567' },
          { icon: '📍', label: 'الموقع', value: 'الرياض، حي العليا' },
        ].map((c, i) => (
          <div key={i} className="glass-card" style={{ borderRadius: 14, padding: 20, textAlign: 'center' }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>{c.icon}</div>
            <div style={{ color: '#d4a017', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{c.label}</div>
            <div style={{ color: '#fff', fontSize: 14, fontWeight: 600 }}>{c.value}</div>
          </div>
        ))}
      </div>

      {sent ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
          <h3 style={{ color: '#fff', fontWeight: 700 }}>تم إرسال رسالتك بنجاح!</h3>
          <p style={{ color: '#9ca3af' }}>سنتواصل معك قريباً</p>
        </div>
      ) : (
        <div className="glass-card" style={{ borderRadius: 20, padding: 32 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 6 }}>الاسم</label>
              <input type="text" placeholder="اسمك الكريم" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 6 }}>رقم الجوال</label>
              <input type="tel" placeholder="05XXXXXXXX" value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 6 }}>الرسالة</label>
              <textarea
                placeholder="استفسارك أو طلبك..."
                value={form.message}
                onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
                rows={4}
                style={{
                  background: 'rgba(6,13,31,0.8)',
                  border: '1px solid rgba(212,160,23,0.3)',
                  color: 'white',
                  borderRadius: 8,
                  padding: '10px 14px',
                  width: '100%',
                  outline: 'none',
                  resize: 'vertical',
                  fontFamily: 'inherit',
                }}
              />
            </div>
            <button className="gold-btn" style={{ padding: '13px', borderRadius: 10, fontSize: 15 }} onClick={() => setSent(true)}>
              إرسال الرسالة 📨
            </button>
          </div>
        </div>
      )}
    </section>
  )
}

// ─── Footer ───────────────────────────────────────────────────────────────────

function Footer({ setCurrentPage }) {
  return (
    <footer style={{
      background: 'rgba(6,13,31,0.95)',
      borderTop: '1px solid rgba(212,160,23,0.15)',
      padding: '48px 24px 24px',
      marginTop: 80,
    }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 40, marginBottom: 40 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <div style={{ width: 36, height: 36, background: 'linear-gradient(135deg, #d4a017, #f0c040)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <CarIcon size={18} color="#060d1f" />
              </div>
              <span style={{ fontWeight: 800, color: '#fff', fontSize: 16 }}>مكتب الهدى</span>
            </div>
            <p style={{ color: '#6b7280', fontSize: 14, lineHeight: 1.7 }}>
              نوفر أفضل تجربة تأجير سيارات بأعلى معايير الجودة والأمان.
            </p>
          </div>
          <div>
            <h4 style={{ color: '#d4a017', fontSize: 14, fontWeight: 700, marginBottom: 16 }}>روابط سريعة</h4>
            {['الرئيسية', 'معرض السيارات', 'عن المكتب', 'تواصل معنا'].map((l, i) => (
              <div key={i} style={{ marginBottom: 8 }}>
                <span
                  className="nav-link"
                  style={{ fontSize: 14 }}
                  onClick={() => setCurrentPage(['home', 'cars', 'about', 'contact'][i])}
                >
                  {l}
                </span>
              </div>
            ))}
          </div>
          <div>
            <h4 style={{ color: '#d4a017', fontSize: 14, fontWeight: 700, marginBottom: 16 }}>تواصل معنا</h4>
            <div style={{ color: '#9ca3af', fontSize: 14, lineHeight: 2 }}>
              <div>📞 0501234567</div>
              <div>💬 واتساب: 0501234567</div>
              <div>📍 الرياض، حي العليا</div>
              <div>🕐 من 8 ص حتى 10 م</div>
            </div>
          </div>
        </div>
        <div style={{ borderTop: '1px solid rgba(212,160,23,0.1)', paddingTop: 20, textAlign: 'center', color: '#4b5563', fontSize: 13 }}>
          © 2026 مكتب الهدى لتأجير السيارات · جميع الحقوق محفوظة
        </div>
      </div>
    </footer>
  )
}

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  const [currentPage, setCurrentPage] = useState('home')
  const [bookingCar, setBookingCar] = useState(null)
  const [bookings, setBookings] = useState([])
  const [searchFilter, setSearchFilter] = useState(null)

  const handleSearch = useCallback((filter) => {
    setSearchFilter(filter)
  }, [])

  const handleBookCar = useCallback((car) => {
    setBookingCar(car)
  }, [])

  const handleConfirmBooking = useCallback((data) => {
    const newBooking = {
      id: `BK${String(Date.now()).slice(-4)}`,
      name: data.name,
      phone: data.phone,
      car: data.car.name,
      days: data.days,
      total: data.total,
      status: 'pending',
      date: new Date().toISOString().split('T')[0],
    }
    setBookings(prev => [...prev, newBooking])
  }, [])

  return (
    <div style={{ minHeight: '100vh', background: '#060d1f' }}>
      <Navbar currentPage={currentPage} setCurrentPage={setCurrentPage} />

      {currentPage === 'home' && (
        <>
          <HeroSection onSearch={handleSearch} setCurrentPage={setCurrentPage} />
          <CarGallery searchFilter={searchFilter} onBookCar={handleBookCar} />
        </>
      )}

      {currentPage === 'cars' && (
        <CarGallery searchFilter={searchFilter} onBookCar={handleBookCar} />
      )}

      {currentPage === 'about' && <AboutPage />}

      {currentPage === 'contact' && <ContactPage />}

      {currentPage === 'dashboard' && <Dashboard bookings={bookings} />}

      <Footer setCurrentPage={setCurrentPage} />

      {bookingCar && (
        <BookingModal
          car={bookingCar}
          onClose={() => setBookingCar(null)}
          onConfirm={(data) => {
            handleConfirmBooking(data)
          }}
        />
      )}
    </div>
  )
}
