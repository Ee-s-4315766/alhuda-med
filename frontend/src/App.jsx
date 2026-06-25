import { useState, useEffect, useCallback, useRef } from 'react'
import { supabase, isConfigured } from './lib/supabase'
import {
  fetchCars, fetchBookings, createBooking, deleteCar,
  subscribeToBookings, signIn, signOut, onAuthChange,
  notifyWhatsApp,
} from './lib/db'
import './index.css'

// ─── Static fallback data (demo mode when Supabase not configured) ────────────

const DEMO_CARS = [
  { id: '1', name: 'تويوتا كامري',      type: 'sedan',   type_label: 'سيدان',     price: 150, seats: 5, year: 2024, fuel: 'بنزين', transmission: 'أوتوماتيك', available: true,  color: '#1a3a6b', features: ['بلوتوث', 'كاميرا خلفية', 'تحكم بالمحرك'],   image_url: 'https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb' },
  { id: '2', name: 'BMW الفئة الخامسة', type: 'sedan',   type_label: 'سيدان',     price: 380, seats: 5, year: 2024, fuel: 'بنزين', transmission: 'أوتوماتيك', available: true,  color: '#2a1a4a', features: ['شاشة لمس', 'تحكم بالصوت', 'مقاعد جلد', 'نظام ملاحة'], image_url: 'https://images.unsplash.com/photo-1555215695-3004980ad54e' },
  { id: '3', name: 'هيونداي توسان',     type: 'suv',     type_label: 'دفع رباعي', price: 200, seats: 5, year: 2023, fuel: 'بنزين', transmission: 'أوتوماتيك', available: true,  color: '#1a4a2a', features: ['دفع رباعي', 'فتحة سقف', 'كاميرا 360'],         image_url: 'https://images.unsplash.com/photo-1625047509252-ab38fb5c7343' },
  { id: '4', name: 'تويوتا لاند كروزر', type: 'suv',    type_label: 'دفع رباعي', price: 550, seats: 7, year: 2024, fuel: 'ديزل',  transmission: 'أوتوماتيك', available: false, color: '#3a1a1a', features: ['7 مقاعد', 'دفع رباعي', 'شاشة 12"', 'مقاعد مدفأة'], image_url: 'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b' },
  { id: '5', name: 'كيا بيكانتو',       type: 'economy', type_label: 'اقتصادية',  price: 80,  seats: 5, year: 2023, fuel: 'بنزين', transmission: 'أوتوماتيك', available: true,  color: '#1a3a3a', features: ['اقتصادي بالوقود', 'سهل القيادة', 'موقف سهل'],  image_url: 'https://images.unsplash.com/photo-1541899481282-d53bffe3c35d' },
  { id: '6', name: 'هيونداي إيلانترا',  type: 'economy', type_label: 'اقتصادية',  price: 110, seats: 5, year: 2024, fuel: 'بنزين', transmission: 'أوتوماتيك', available: true,  color: '#1a2a4a', features: ['بلوتوث', 'شاشة لمس', 'USB'],                    image_url: 'https://images.unsplash.com/photo-1494976388531-d1058494cdd8' },
]

const DEMO_BOOKINGS = [
  { id: 'BK001', car_name: 'تويوتا لاند كروزر', customer_name: 'أحمد محمد السعيد',   customer_phone: '0501234567', days: 3, total: 1650, status: 'active',    created_at: '2026-06-20' },
  { id: 'BK002', car_name: 'BMW الفئة الخامسة',  customer_name: 'سارة عبدالله الأحمد', customer_phone: '0559876543', days: 5, total: 1900, status: 'pending',   created_at: '2026-06-22' },
  { id: 'BK003', car_name: 'هيونداي توسان',      customer_name: 'محمد علي الزهراني',   customer_phone: '0531112233', days: 2, total: 400,  status: 'completed', created_at: '2026-06-18' },
]

// ─── Icons ────────────────────────────────────────────────────────────────────

const CarIcon = ({ size = 24, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 17H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v9a2 2 0 0 1-2 2h-2"/>
    <circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>
    <path d="M13 2v5h5"/>
  </svg>
)
const CalendarIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
  </svg>
)
const CloseIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
)
const CheckIcon = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)
const StarIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="#f0b429" stroke="#f0b429" strokeWidth="1">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
  </svg>
)
const RefreshIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
)
const BellIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
  </svg>
)
const LogOutIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
)

const TrashIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
  </svg>
)

// ─── Car SVG Illustration ─────────────────────────────────────────────────────

const CarIllustration = ({ color = '#1a3a6b', type = 'sedan' }) => {
  const uid = `${type}-${color.replace('#', '')}`
  if (type === 'suv') return (
    <svg viewBox="0 0 200 100" width="160" height="80">
      <defs>
        <linearGradient id={`g1-${uid}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: color }} /><stop offset="100%" style={{ stopColor: '#091747' }} />
        </linearGradient>
      </defs>
      <rect x="20" y="30" width="160" height="45" rx="8" fill={`url(#g1-${uid})`}/>
      <rect x="30" y="15" width="130" height="30" rx="6" fill={`url(#g1-${uid})`} opacity="0.8"/>
      <rect x="35" y="18" width="50" height="22" rx="4" fill="rgba(120,200,255,0.3)" stroke="rgba(120,200,255,0.5)" strokeWidth="1"/>
      <rect x="95" y="18" width="55" height="22" rx="4" fill="rgba(120,200,255,0.3)" stroke="rgba(120,200,255,0.5)" strokeWidth="1"/>
      <circle cx="55" cy="78" r="14" fill="#091747" stroke="#f0b429" strokeWidth="2"/>
      <circle cx="55" cy="78" r="8" fill="#0d2260"/>
      <circle cx="145" cy="78" r="14" fill="#091747" stroke="#f0b429" strokeWidth="2"/>
      <circle cx="145" cy="78" r="8" fill="#0d2260"/>
      <rect x="20" y="42" width="12" height="8" rx="2" fill="#ffd04d"/>
      <rect x="168" y="42" width="12" height="8" rx="2" fill="rgba(255,50,50,0.8)"/>
    </svg>
  )
  if (type === 'economy') return (
    <svg viewBox="0 0 200 100" width="160" height="80">
      <defs>
        <linearGradient id={`g2-${uid}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: color }} /><stop offset="100%" style={{ stopColor: '#091747' }} />
        </linearGradient>
      </defs>
      <rect x="25" y="40" width="150" height="38" rx="6" fill={`url(#g2-${uid})`}/>
      <path d="M60 40 Q80 20 120 20 Q150 20 160 40" fill={`url(#g2-${uid})`} opacity="0.8"/>
      <rect x="65" y="22" width="40" height="20" rx="4" fill="rgba(120,200,255,0.3)" stroke="rgba(120,200,255,0.5)" strokeWidth="1"/>
      <rect x="110" y="22" width="40" height="20" rx="4" fill="rgba(120,200,255,0.3)" stroke="rgba(120,200,255,0.5)" strokeWidth="1"/>
      <circle cx="60" cy="78" r="13" fill="#091747" stroke="#f0b429" strokeWidth="2"/>
      <circle cx="60" cy="78" r="7" fill="#0d2260"/>
      <circle cx="140" cy="78" r="13" fill="#091747" stroke="#f0b429" strokeWidth="2"/>
      <circle cx="140" cy="78" r="7" fill="#0d2260"/>
      <rect x="25" y="48" width="10" height="7" rx="2" fill="#ffd04d"/>
      <rect x="165" y="48" width="10" height="7" rx="2" fill="rgba(255,50,50,0.8)"/>
    </svg>
  )
  return (
    <svg viewBox="0 0 200 100" width="160" height="80">
      <defs>
        <linearGradient id={`g3-${uid}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: color }} /><stop offset="100%" style={{ stopColor: '#091747' }} />
        </linearGradient>
      </defs>
      <rect x="15" y="38" width="170" height="40" rx="8" fill={`url(#g3-${uid})`}/>
      <path d="M50 38 Q75 18 125 18 Q155 18 165 38" fill={`url(#g3-${uid})`} opacity="0.85"/>
      <rect x="58" y="20" width="42" height="20" rx="3" fill="rgba(120,200,255,0.35)" stroke="rgba(120,200,255,0.6)" strokeWidth="1"/>
      <rect x="105" y="20" width="48" height="20" rx="3" fill="rgba(120,200,255,0.35)" stroke="rgba(120,200,255,0.6)" strokeWidth="1"/>
      <circle cx="52" cy="78" r="14" fill="#091747" stroke="#f0b429" strokeWidth="2.5"/>
      <circle cx="52" cy="78" r="8" fill="#0d2260"/>
      <circle cx="148" cy="78" r="14" fill="#091747" stroke="#f0b429" strokeWidth="2.5"/>
      <circle cx="148" cy="78" r="8" fill="#0d2260"/>
      <rect x="15" y="46" width="14" height="9" rx="3" fill="#ffd04d" opacity="0.9"/>
      <rect x="171" y="46" width="14" height="9" rx="3" fill="rgba(255,50,50,0.9)"/>
    </svg>
  )
}

// ─── Car Image (real photo with SVG fallback) ─────────────────────────────────

function CarImage({ car }) {
  const [errored, setErrored] = useState(false)
  if (!car.image_url || errored) {
    return <CarIllustration color={car.color} type={car.type} />
  }
  return (
    <img
      src={`${car.image_url}?auto=format&fit=crop&w=500&q=80`}
      alt={car.name}
      onError={() => setErrored(true)}
      style={{
        width: '100%', height: '100%',
        objectFit: 'cover', borderRadius: 8,
        transition: 'transform 0.4s ease',
      }}
    />
  )
}

// ─── Moyasar Payment Step ─────────────────────────────────────────────────────

function PaymentStep({ total, carName, onConfirm, onBack, submitting }) {
  const containerRef = useRef(null)
  const moyasarKey = import.meta.env.VITE_MOYASAR_KEY
  const hasMoyasar = Boolean(moyasarKey) && Boolean(window.Moyasar)

  useEffect(() => {
    if (!hasMoyasar || !containerRef.current) return
    containerRef.current.innerHTML = ''
    window.Moyasar.init({
      element: containerRef.current,
      amount: total * 100,
      currency: 'SAR',
      description: `حجز ${carName} — مكتب موكار`,
      publishable_api_key: moyasarKey,
      callback_url: window.location.href,
      methods: ['creditcard', 'applepay', 'stcpay'],
      on_completed: (payment) => {
        if (payment.status === 'paid') onConfirm({ payment })
      },
    })
    return () => { if (containerRef.current) containerRef.current.innerHTML = '' }
  }, [total, carName, hasMoyasar, moyasarKey])

  return (
    <div>
      <p style={{ color: '#f0b429', fontSize: 13, fontWeight: 600, margin: '0 0 20px' }}>
        3️⃣ الدفع الإلكتروني
      </p>

      {/* Price summary */}
      <div style={{
        background: 'rgba(212,160,23,0.06)', border: '1px solid rgba(212,160,23,0.2)',
        borderRadius: 12, padding: 16, marginBottom: 20, display: 'flex',
        justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div>
          <div style={{ color: '#9ca3af', fontSize: 12 }}>المبلغ الإجمالي</div>
          <div style={{ color: '#f0b429', fontSize: 28, fontWeight: 900 }}>{total} <span style={{ fontSize: 14 }}>ر.س</span></div>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          {['mada', 'VISA', 'MC', 'STC', ''].map((m, i) => (
            i < 4 ? (
              <span key={i} style={{
                background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 6, padding: '4px 10px', fontSize: 11, color: '#9ca3af', fontWeight: 700,
              }}>{m}</span>
            ) : null
          ))}
        </div>
      </div>

      {hasMoyasar ? (
        <div ref={containerRef} style={{ minHeight: 200 }} />
      ) : (
        <div style={{ marginBottom: 20 }}>
          {!moyasarKey ? (
            <div style={{
              background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.3)',
              borderRadius: 10, padding: '12px 16px', color: '#fbbf24', fontSize: 13, marginBottom: 16,
              lineHeight: 1.6,
            }}>
              ⚠️ وضع تجريبي — لتفعيل بوابة الدفع الحقيقية أضف<br/>
              <code style={{ background: 'rgba(0,0,0,0.3)', padding: '1px 6px', borderRadius: 4, fontSize: 11 }}>VITE_MOYASAR_KEY</code> في ملف <code style={{ background: 'rgba(0,0,0,0.3)', padding: '1px 6px', borderRadius: 4, fontSize: 11 }}>.env</code>
            </div>
          ) : (
            <div style={{ color: '#9ca3af', fontSize: 13, marginBottom: 16, textAlign: 'center' }}>
              ⏳ جاري تحميل بوابة الدفع...
            </div>
          )}
          <button
            className="gold-btn"
            style={{ width: '100%', padding: '13px', borderRadius: 10, fontSize: 15, opacity: submitting ? 0.7 : 1 }}
            disabled={submitting}
            onClick={() => onConfirm({ payment: { status: 'demo' } })}
          >
            {submitting ? '⏳ جاري الحفظ...' : '✅ تأكيد الحجز (تجريبي)'}
          </button>
        </div>
      )}

      <button onClick={onBack} style={{
        width: '100%', padding: '10px', borderRadius: 10, fontSize: 13, marginTop: 8,
        background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)',
        color: '#9ca3af', cursor: 'pointer',
      }}>
        → رجوع
      </button>
    </div>
  )
}

// ─── Notification toast ───────────────────────────────────────────────────────

function Toast({ message, type = 'success', onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 4000)
    return () => clearTimeout(t)
  }, [onClose])

  const colors = {
    success: { bg: 'rgba(34,197,94,0.15)', border: 'rgba(34,197,94,0.4)', icon: '✅' },
    error:   { bg: 'rgba(239,68,68,0.15)',  border: 'rgba(239,68,68,0.4)',  icon: '❌' },
    info:    { bg: 'rgba(96,165,250,0.15)', border: 'rgba(96,165,250,0.4)', icon: '🔔' },
  }
  const c = colors[type]
  return (
    <div style={{
      position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)',
      zIndex: 2000, background: c.bg, border: `1px solid ${c.border}`,
      borderRadius: 12, padding: '14px 20px', backdropFilter: 'blur(12px)',
      display: 'flex', alignItems: 'center', gap: 10, minWidth: 280,
      animation: 'fadeIn 0.3s ease-out', boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
    }}>
      <span style={{ fontSize: 18 }}>{c.icon}</span>
      <span style={{ color: '#fff', fontSize: 14, flex: 1 }}>{message}</span>
      <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', padding: 4 }}>
        <CloseIcon />
      </button>
    </div>
  )
}

// ─── Config banner (when Supabase not set up yet) ─────────────────────────────

function ConfigBanner() {
  const [open, setOpen] = useState(true)
  if (!open) return null
  return (
    <div style={{
      background: 'rgba(212,160,23,0.08)',
      border: '1px solid rgba(212,160,23,0.3)',
      borderRadius: 0,
      padding: '12px 24px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      gap: 16, flexWrap: 'wrap',
    }}>
      <span style={{ color: '#f0b429', fontSize: 13 }}>
        ⚠️ وضع العرض التجريبي — أضف <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: 4, fontSize: 12 }}>VITE_SUPABASE_URL</code> و <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: 4, fontSize: 12 }}>VITE_SUPABASE_ANON_KEY</code> في ملف <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: 4, fontSize: 12 }}>.env</code> لتفعيل قاعدة البيانات
      </span>
      <button onClick={() => setOpen(false)} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', padding: 4 }}>
        <CloseIcon />
      </button>
    </div>
  )
}

// ─── Navbar ───────────────────────────────────────────────────────────────────

function Navbar({ currentPage, setCurrentPage, pendingCount, session }) {
  return (
    <nav style={{
      background: 'rgba(6,13,31,0.97)',
      borderBottom: '1px solid rgba(212,160,23,0.2)',
      backdropFilter: 'blur(12px)',
      position: 'sticky', top: 0, zIndex: 100,
    }}>
      <div style={{
        maxWidth: 1200, margin: '0 auto', padding: '0 24px',
        height: 70, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}
          onClick={() => setCurrentPage('home')}>
          <img src="/logo.jpg" alt="MOCAR Rental"
            style={{ height: 48, width: 'auto', borderRadius: 8, objectFit: 'contain' }} />
        </div>

        <div style={{ display: 'flex', gap: 28, alignItems: 'center' }}>
          {[['home', 'الرئيسية'], ['cars', 'معرض السيارات'], ['about', 'عن المكتب'], ['contact', 'تواصل معنا']].map(([id, label]) => (
            <span key={id} className="nav-link"
              style={{ fontWeight: currentPage === id ? 600 : 400, fontSize: 14 }}
              onClick={() => setCurrentPage(id)}>
              {label}
            </span>
          ))}
          <button className="gold-btn" style={{ padding: '8px 18px', borderRadius: 8, fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}
            onClick={() => setCurrentPage('dashboard')}>
            {pendingCount > 0 && (
              <span style={{
                background: '#ef4444', color: '#fff', borderRadius: '50%',
                width: 18, height: 18, display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 10, fontWeight: 900,
              }}>{pendingCount}</span>
            )}
            لوحة التحكم
          </button>
        </div>
      </div>
    </nav>
  )
}

// ─── Hero Section ─────────────────────────────────────────────────────────────

function HeroSection({ onSearch, setCurrentPage }) {
  const today = new Date().toISOString().split('T')[0]
  const [form, setForm] = useState({ pickup: today, dropoff: '', carType: 'all' })

  const handleSearch = (e) => {
    e.preventDefault()
    onSearch(form)
    setCurrentPage('cars')
  }

  return (
    <section className="hero-bg" style={{ minHeight: '88vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '60px 24px' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto', width: '100%', position: 'relative', zIndex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
          <span style={{ background: 'rgba(212,160,23,0.1)', border: '1px solid rgba(212,160,23,0.4)', color: '#f0b429', padding: '6px 20px', borderRadius: 20, fontSize: 13, fontWeight: 600, letterSpacing: 1 }}>
            ✦ مكتب موكار لتأجير السيارات ✦
          </span>
        </div>
        <h1 style={{ textAlign: 'center', fontSize: 'clamp(36px, 6vw, 70px)', fontWeight: 900, lineHeight: 1.15, margin: '0 0 16px', color: '#fff' }}>
          تجربة قيادة{' '}
          <span style={{ background: 'linear-gradient(135deg, #f0b429, #ffd04d)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
            استثنائية
          </span>
        </h1>
        <p style={{ textAlign: 'center', fontSize: 'clamp(15px, 2vw, 19px)', color: '#9ca3af', margin: '0 0 48px', lineHeight: 1.7 }}>
          أفضل سيارات الفئة الأولى · تأمين شامل · خدمة 24/7
        </p>

        <form onSubmit={handleSearch}>
          <div style={{
            background: 'rgba(13,31,60,0.9)', backdropFilter: 'blur(20px)',
            border: '1px solid rgba(212,160,23,0.3)', borderRadius: 20,
            padding: 'clamp(20px, 4vw, 36px)', boxShadow: '0 24px 80px rgba(0,0,0,0.4)',
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20, marginBottom: 24 }}>
              <div>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#f0b429', fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
                  <CalendarIcon size={13} /> تاريخ الاستلام
                </label>
                <input type="date" value={form.pickup} min={today} required
                  onChange={e => setForm(f => ({ ...f, pickup: e.target.value }))} />
              </div>
              <div>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#f0b429', fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
                  <CalendarIcon size={13} /> تاريخ التسليم
                </label>
                <input type="date" value={form.dropoff} min={form.pickup || today} required
                  onChange={e => setForm(f => ({ ...f, dropoff: e.target.value }))} />
              </div>
              <div>
                <label style={{ display: 'block', color: '#f0b429', fontSize: 13, fontWeight: 600, marginBottom: 8 }}>نوع السيارة</label>
                <select value={form.carType} onChange={e => setForm(f => ({ ...f, carType: e.target.value }))}>
                  <option value="all">جميع الأنواع</option>
                  <option value="sedan">سيدان</option>
                  <option value="suv">دفع رباعي SUV</option>
                  <option value="economy">اقتصادية</option>
                </select>
              </div>
            </div>
            <button type="submit" className="gold-btn" style={{ width: '100%', padding: '14px', borderRadius: 12, fontSize: 17, letterSpacing: 0.5 }}>
              ابحث عن سيارتك المثالية ←
            </button>
          </div>
        </form>

      </div>
    </section>
  )
}

// ─── Car Gallery ──────────────────────────────────────────────────────────────

function CarGallery({ searchFilter, onBookCar, cars, loading }) {
  const [activeFilter, setActiveFilter] = useState(searchFilter?.carType || 'all')

  const filtered = cars.filter(c => activeFilter === 'all' || c.type === activeFilter)

  return (
    <section style={{ padding: '80px 24px', maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <span style={{ color: '#f0b429', fontSize: 13, fontWeight: 600, letterSpacing: 2 }}>أسطولنا</span>
        <h2 style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 800, margin: '12px 0 16px', color: '#fff' }}>اختر سيارتك المثالية</h2>
        <p style={{ color: '#6b7280', fontSize: 16, maxWidth: 500, margin: '0 auto' }}>مجموعة متنوعة من أرقى السيارات لتلبية جميع احتياجاتك</p>
      </div>

      <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginBottom: 40, flexWrap: 'wrap' }}>
        {[['all', 'الكل'], ['sedan', 'سيدان'], ['suv', 'دفع رباعي SUV'], ['economy', 'اقتصادية']].map(([k, l]) => (
          <button key={k} className={`filter-btn ${activeFilter === k ? 'active' : ''}`} onClick={() => setActiveFilter(k)}>{l}</button>
        ))}
      </div>

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 24 }}>
          {[1,2,3,4,5,6].map(i => (
            <div key={i} style={{ background: 'rgba(13,31,60,0.5)', borderRadius: 20, height: 380, animation: 'pulse 1.5s ease-in-out infinite' }} />
          ))}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 24 }}>
          {filtered.map((car, idx) => (
            <CarCard key={car.id} car={car} idx={idx} onBook={() => onBookCar(car)} />
          ))}
        </div>
      )}
    </section>
  )
}

function CarCard({ car, idx, onBook }) {
  return (
    <div className="car-card animate-fade-in" style={{ animationDelay: `${idx * 0.08}s` }}>
      {/* Car image area */}
      <div style={{
        background: `linear-gradient(135deg, ${car.color}44 0%, #0b1d54 100%)`,
        height: 200, position: 'relative', overflow: 'hidden',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <CarImage car={car} />
        <div style={{ position: 'absolute', top: 12, right: 12 }}>
          <span className={car.available ? 'badge-available' : 'badge-rented'}>
            {car.available ? '● متاحة' : '● مؤجرة'}
          </span>
        </div>
        <div style={{
          position: 'absolute', top: 12, left: 12,
          background: 'rgba(6,13,31,0.7)', border: '1px solid rgba(212,160,23,0.3)',
          borderRadius: 6, padding: '3px 10px', fontSize: 11, color: '#f0b429', backdropFilter: 'blur(4px)',
        }}>
          {car.type_label}
        </div>
        <div style={{ position: 'absolute', bottom: 8, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 2 }}>
          {[1,2,3,4,5].map(s => <StarIcon key={s} />)}
        </div>
      </div>
      <div style={{ padding: '20px 20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: '#fff' }}>{car.name}</h3>
            <span style={{ fontSize: 12, color: '#6b7280' }}>{car.year} · {car.fuel} · {car.transmission}</span>
          </div>
          <div style={{ textAlign: 'left' }}>
            <span style={{ fontSize: 22, fontWeight: 900, color: '#f0b429' }}>{car.price}</span>
            <span style={{ fontSize: 11, color: '#6b7280' }}> ر.س/يوم</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 12, marginBottom: 14 }}>
          {[`👤 ${car.seats}`, `⚙️ ${car.transmission}`, `⛽ ${car.fuel}`].map((s, i) => (
            <span key={i} style={{ fontSize: 11, color: '#9ca3af' }}>{s}</span>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 18 }}>
          {(car.features || []).slice(0, 3).map((f, i) => (
            <span key={i} style={{
              fontSize: 11, padding: '3px 10px', borderRadius: 12,
              background: 'rgba(212,160,23,0.08)', color: '#f0b429', border: '1px solid rgba(212,160,23,0.2)',
            }}>{f}</span>
          ))}
        </div>
        <button
          className="gold-btn"
          style={{ width: '100%', padding: '12px', borderRadius: 10, fontSize: 14, opacity: car.available ? 1 : 0.5, cursor: car.available ? 'pointer' : 'not-allowed' }}
          disabled={!car.available}
          onClick={onBook}
        >
          {car.available ? '🔑 احجز الآن' : '⏳ غير متاحة حالياً'}
        </button>
      </div>
    </div>
  )
}

// ─── Booking Modal ────────────────────────────────────────────────────────────

function BookingModal({ car, onClose, onConfirm }) {
  const today = new Date().toISOString().split('T')[0]
  const [step, setStep] = useState(1)
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ name: '', phone: '', idNumber: '', licenseNumber: '', pickup: today, dropoff: '' })

  const days = form.pickup && form.dropoff
    ? Math.max(1, Math.ceil((new Date(form.dropoff) - new Date(form.pickup)) / 86400000))
    : 1
  const total = car.price * days
  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }))

  const handlePaymentConfirm = async ({ payment }) => {
    setSubmitting(true)
    setError('')
    try {
      await onConfirm({
        carId: car.id, carName: car.name,
        name: form.name, phone: form.phone,
        idNumber: form.idNumber, licenseNumber: form.licenseNumber,
        pickup: form.pickup, dropoff: form.dropoff,
        days, pricePerDay: car.price, total,
        paymentId: payment?.id || 'demo',
        paymentStatus: payment?.status || 'demo',
      })
      setSubmitted(true)
    } catch (err) {
      setError(err.message || 'حدث خطأ، يرجى المحاولة مجدداً')
    } finally {
      setSubmitting(false)
    }
  }

  if (submitted) return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ textAlign: 'center' }}>
        <div style={{ width: 72, height: 72, background: 'linear-gradient(135deg, #22c55e, #16a34a)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
          <CheckIcon size={32} />
        </div>
        <h2 style={{ color: '#fff', fontSize: 22, fontWeight: 800, marginBottom: 8 }}>تم الحجز بنجاح! 🎉</h2>
        <p style={{ color: '#9ca3af', lineHeight: 1.7, marginBottom: 24 }}>
          تم حفظ حجزك وسيصلك تأكيد على واتساب خلال دقائق.
        </p>
        <div style={{ background: 'rgba(212,160,23,0.08)', border: '1px solid rgba(212,160,23,0.2)', borderRadius: 12, padding: 20, marginBottom: 24 }}>
          {[['السيارة', car.name], ['الاستلام', form.pickup], ['التسليم', form.dropoff], ['عدد الأيام', `${days} يوم`]].map(([l, v]) => (
            <div key={l} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ color: '#6b7280', fontSize: 13 }}>{l}</span>
              <span style={{ color: '#fff', fontWeight: 600, fontSize: 13 }}>{v}</span>
            </div>
          ))}
          <div style={{ borderTop: '1px solid rgba(212,160,23,0.2)', paddingTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: '#f0b429', fontWeight: 700 }}>الإجمالي</span>
            <span style={{ color: '#f0b429', fontWeight: 900, fontSize: 24 }}>{total} ر.س</span>
          </div>
        </div>
        {/* WhatsApp CTA */}
        <a
          href={`https://wa.me/966501234567?text=${encodeURIComponent(`مرحباً، أريد تأكيد حجزي لـ ${car.name} من ${form.pickup} إلى ${form.dropoff}`)}`}
          target="_blank" rel="noopener noreferrer"
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            background: 'rgba(37,211,102,0.1)', border: '1px solid rgba(37,211,102,0.3)',
            borderRadius: 10, padding: '12px 20px', color: '#25d366',
            textDecoration: 'none', fontWeight: 600, fontSize: 14, marginBottom: 12,
          }}
        >
          💬 تواصل معنا على واتساب
        </a>
        <button className="gold-btn" style={{ width: '100%', padding: '12px', borderRadius: 10, fontSize: 15 }} onClick={onClose}>
          حسناً، شكراً!
        </button>
      </div>
    </div>
  )

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: '#fff' }}>استمارة الحجز</h2>
            <p style={{ margin: '4px 0 0', color: '#f0b429', fontSize: 13 }}>{car.name}</p>
          </div>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: 8, cursor: 'pointer', color: '#9ca3af' }}>
            <CloseIcon />
          </button>
        </div>

        {/* Progress bar — 3 steps */}
        <div style={{ display: 'flex', gap: 6, marginBottom: 24 }}>
          {[1, 2, 3].map(s => (
            <div key={s} style={{
              flex: 1, height: 4, borderRadius: 2,
              background: step >= s ? 'linear-gradient(90deg, #f0b429, #ffd04d)' : 'rgba(255,255,255,0.1)',
              transition: 'background 0.3s',
            }} />
          ))}
        </div>

        {error && (
          <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '10px 14px', marginBottom: 16, color: '#f87171', fontSize: 13 }}>
            {error}
          </div>
        )}

        {/* Step 1: Customer info */}
        {step === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <p style={{ color: '#f0b429', fontSize: 13, fontWeight: 600, margin: 0 }}>1️⃣ بيانات المستأجر</p>
            {[
              { label: 'الاسم الكامل *',         field: 'name',          type: 'text', ph: 'أحمد محمد السعيد' },
              { label: 'رقم الجوال *',           field: 'phone',         type: 'tel',  ph: '05XXXXXXXX' },
              { label: 'رقم الهوية / الإقامة *', field: 'idNumber',      type: 'text', ph: 'XXXXXXXXXX' },
              { label: 'رقم رخصة القيادة *',     field: 'licenseNumber', type: 'text', ph: 'XXXXXXXXX' },
            ].map(({ label, field, type, ph }) => (
              <div key={field}>
                <label style={{ display: 'block', color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>{label}</label>
                <input type={type} placeholder={ph} value={form[field]} onChange={set(field)} required />
              </div>
            ))}
            <button type="button" className="gold-btn"
              style={{ padding: '13px', borderRadius: 10, fontSize: 15, marginTop: 8 }}
              onClick={() => { if (form.name && form.phone && form.idNumber && form.licenseNumber) setStep(2) }}>
              التالي: تحديد التواريخ ←
            </button>
          </div>
        )}

        {/* Step 2: Dates + price summary */}
        {step === 2 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <p style={{ color: '#f0b429', fontSize: 13, fontWeight: 600, margin: 0 }}>2️⃣ تفاصيل الحجز</p>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>تاريخ الاستلام *</label>
              <input type="date" value={form.pickup} min={today} required onChange={set('pickup')} />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>تاريخ التسليم *</label>
              <input type="date" value={form.dropoff} min={form.pickup || today} required onChange={set('dropoff')} />
            </div>
            {form.dropoff && (
              <div style={{ background: 'rgba(212,160,23,0.06)', border: '1px solid rgba(212,160,23,0.2)', borderRadius: 12, padding: 16 }}>
                {[['سعر اليوم', `${car.price} ر.س`], ['عدد الأيام', `${days} يوم`], ['التأمين الشامل', '✓ مشمول']].map(([l, v]) => (
                  <div key={l} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span style={{ color: '#9ca3af', fontSize: 13 }}>{l}</span>
                    <span style={{ color: l === 'التأمين الشامل' ? '#4ade80' : '#fff', fontSize: 13 }}>{v}</span>
                  </div>
                ))}
                <div style={{ borderTop: '1px solid rgba(212,160,23,0.2)', paddingTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#f0b429', fontWeight: 700 }}>الإجمالي</span>
                  <span style={{ color: '#f0b429', fontWeight: 900, fontSize: 24 }}>{total} <span style={{ fontSize: 13 }}>ر.س</span></span>
                </div>
              </div>
            )}
            <div style={{ display: 'flex', gap: 12 }}>
              <button type="button" onClick={() => setStep(1)} style={{ flex: 1, padding: '12px', borderRadius: 10, fontSize: 13, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#9ca3af', cursor: 'pointer' }}>
                → رجوع
              </button>
              <button type="button" className="gold-btn"
                style={{ flex: 2, padding: '13px', borderRadius: 10, fontSize: 15 }}
                disabled={!form.dropoff}
                onClick={() => form.dropoff && setStep(3)}>
                التالي: الدفع ←
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Payment */}
        {step === 3 && (
          <PaymentStep
            total={total}
            carName={car.name}
            onConfirm={handlePaymentConfirm}
            onBack={() => setStep(2)}
            submitting={submitting}
          />
        )}
      </div>
    </div>
  )
}

// ─── Admin Login ──────────────────────────────────────────────────────────────

function AdminLogin({ onLogin }) {
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await signIn(form.email, form.password)
      onLogin()
    } catch (err) {
      setError('بيانات الدخول غير صحيحة')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div style={{
        background: 'linear-gradient(135deg, #0d2260 0%, #0b1d54 100%)',
        border: '1px solid rgba(212,160,23,0.3)',
        borderRadius: 20, padding: 40, width: '100%', maxWidth: 420,
        boxShadow: '0 24px 80px rgba(0,0,0,0.5), 0 0 40px rgba(212,160,23,0.08)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ width: 56, height: 56, background: 'linear-gradient(135deg, #f0b429, #ffd04d)', borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
            <CarIcon size={26} color="#0b1d54" />
          </div>
          <h2 style={{ color: '#fff', fontWeight: 800, fontSize: 22, margin: '0 0 6px' }}>دخول المكتب</h2>
          <p style={{ color: '#6b7280', fontSize: 13 }}>لوحة تحكم مكتب موكار · مشغّلة بـ Supabase Auth</p>
        </div>

        {!isConfigured && (
          <div style={{ background: 'rgba(212,160,23,0.08)', border: '1px solid rgba(212,160,23,0.3)', borderRadius: 8, padding: '10px 14px', marginBottom: 20, color: '#f0b429', fontSize: 12 }}>
            ⚠️ Supabase غير مُهيَّأ. سيتم فتح لوحة التحكم في وضع العرض التجريبي.
          </div>
        )}

        {error && (
          <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '10px 14px', marginBottom: 16, color: '#f87171', fontSize: 13 }}>
            {error}
          </div>
        )}

        <form onSubmit={!isConfigured ? (e) => { e.preventDefault(); onLogin() } : handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={{ display: 'block', color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>البريد الإلكتروني</label>
            <input type="email" placeholder="admin@example.com" value={form.email} required={isConfigured}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
          </div>
          <div>
            <label style={{ display: 'block', color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>كلمة المرور</label>
            <input type="password" placeholder="••••••••" value={form.password} required={isConfigured}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
          </div>
          <button type="submit" className="gold-btn" style={{ padding: '13px', borderRadius: 10, fontSize: 15, marginTop: 8, opacity: loading ? 0.7 : 1 }} disabled={loading}>
            {loading ? '⏳ جاري التحقق...' : isConfigured ? '🔐 دخول آمن' : '⚡ دخول تجريبي'}
          </button>
        </form>
      </div>
    </section>
  )
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

function Dashboard({ session, bookings, cars, onSignOut, onRefresh, onDeleteCar, loading }) {
  const [activeTab, setActiveTab] = useState('overview')

  const stats = {
    totalCars:     cars.length,
    availableCars: cars.filter(c => c.available).length,
    rentedCars:    cars.filter(c => !c.available).length,
    totalBookings: bookings.length,
    pendingCount:  bookings.filter(b => b.status === 'pending').length,
    activeCount:   bookings.filter(b => b.status === 'active').length,
    totalRevenue:  bookings.filter(b => b.status !== 'cancelled').reduce((s, b) => s + (b.total || 0), 0),
  }

  const statusMap = {
    pending:   { label: 'معلق',    color: '#fbbf24', bg: 'rgba(251,191,36,0.1)' },
    active:    { label: 'نشط',     color: '#4ade80', bg: 'rgba(74,222,128,0.1)' },
    completed: { label: 'مكتمل',   color: '#60a5fa', bg: 'rgba(96,165,250,0.1)' },
    cancelled: { label: 'ملغي',    color: '#f87171', bg: 'rgba(248,113,113,0.1)' },
  }

  return (
    <section style={{ padding: '40px 24px', maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 26, fontWeight: 800, color: '#fff' }}>لوحة تحكم المكتب</h2>
          <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: 13 }}>
            {isConfigured ? `مرحباً ${session?.user?.email} · Supabase متصل ✓` : 'وضع العرض التجريبي'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button onClick={onRefresh} style={{
            display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px',
            background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 8, color: '#9ca3af', cursor: 'pointer', fontSize: 13,
          }}>
            <RefreshIcon size={14} /> تحديث
          </button>
          {isConfigured && session && (
            <button onClick={onSignOut} style={{
              display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px',
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 8, color: '#f87171', cursor: 'pointer', fontSize: 13,
            }}>
              <LogOutIcon /> خروج
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, background: 'rgba(13,31,60,0.6)', borderRadius: 12, padding: 4, marginBottom: 32, width: 'fit-content' }}>
        {[['overview', '📊 نظرة عامة'], ['bookings', '📋 الطلبات'], ['fleet', '🚗 الأسطول']].map(([id, label]) => (
          <button key={id} onClick={() => setActiveTab(id)} style={{
            padding: '9px 18px', borderRadius: 10, border: 'none', cursor: 'pointer', fontSize: 13,
            fontWeight: activeTab === id ? 700 : 400,
            background: activeTab === id ? 'linear-gradient(135deg, #f0b429, #ffd04d)' : 'transparent',
            color: activeTab === id ? '#0b1d54' : '#9ca3af', transition: 'all 0.3s',
          }}>{label}</button>
        ))}
      </div>

      {/* Overview */}
      {activeTab === 'overview' && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 18, marginBottom: 32 }}>
            {[
              ['🚗', 'إجمالي السيارات', stats.totalCars,     '#60a5fa'],
              ['🔑', 'مؤجرة حالياً',    stats.rentedCars,    '#f87171'],
              ['✅', 'متاحة',           stats.availableCars, '#4ade80'],
              ['⏳', 'طلبات معلقة',     stats.pendingCount,  '#fbbf24'],
              ['📋', 'إجمالي الطلبات',  stats.totalBookings, '#a78bfa'],
              ['💰', 'إجمالي الإيرادات', `${stats.totalRevenue.toLocaleString()} ر.س`, '#f0b429'],
            ].map(([icon, label, value, color]) => (
              <div key={label} className="stat-card">
                <div style={{ fontSize: 28, marginBottom: 10 }}>{icon}</div>
                <div style={{ fontSize: 'clamp(18px, 2.5vw, 28px)', fontWeight: 900, color, marginBottom: 6 }}>{value}</div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>{label}</div>
              </div>
            ))}
          </div>

          {/* Realtime indicator */}
          {isConfigured && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20, color: '#4ade80', fontSize: 13 }}>
              <span style={{ width: 8, height: 8, background: '#4ade80', borderRadius: '50%', animation: 'pulse 2s infinite' }} />
              تحديث فوري مفعّل · Supabase Realtime
            </div>
          )}

          {/* Recent bookings */}
          <BookingsTable bookings={bookings.slice(0, 5)} statusMap={statusMap} title="آخر الطلبات" />
        </>
      )}

      {activeTab === 'bookings' && (
        <BookingsTable bookings={bookings} statusMap={statusMap} title={`جميع الطلبات (${bookings.length})`} showAll />
      )}

      {activeTab === 'fleet' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 18 }}>
          {cars.map((car) => (
            <div key={car.id} style={{
              background: 'rgba(13,31,60,0.7)',
              border: `1px solid ${car.available ? 'rgba(74,222,128,0.2)' : 'rgba(248,113,113,0.2)'}`,
              borderRadius: 16, padding: 18, display: 'flex', gap: 14, alignItems: 'center',
            }}>
              <div style={{ background: `${car.color}22`, borderRadius: 8, padding: 8, flexShrink: 0 }}>
                <CarIllustration color={car.color} type={car.type} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 700, color: '#fff', fontSize: 14 }}>{car.name}</div>
                <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 8 }}>{car.type_label} · {car.year}</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#f0b429', fontWeight: 700, fontSize: 13 }}>{car.price} ر.س/يوم</span>
                  <span className={car.available ? 'badge-available' : 'badge-rented'}>
                    {car.available ? 'متاحة' : 'مؤجرة'}
                  </span>
                </div>
              </div>
              {onDeleteCar && (
                <button
                  onClick={() => { if (window.confirm(`حذف "${car.name}"؟`)) onDeleteCar(car.id) }}
                  style={{
                    flexShrink: 0, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                    borderRadius: 8, color: '#f87171', cursor: 'pointer', padding: '6px 8px',
                    display: 'flex', alignItems: 'center', transition: 'all 0.2s',
                  }}
                  title="حذف السيارة"
                >
                  <TrashIcon />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

function BookingsTable({ bookings, statusMap, title, showAll = false }) {
  const displayed = showAll ? bookings : bookings.slice(0, 5)
  return (
    <div style={{ background: 'rgba(13,31,60,0.6)', border: '1px solid rgba(212,160,23,0.15)', borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ padding: '18px 24px', borderBottom: '1px solid rgba(212,160,23,0.1)' }}>
        <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#fff' }}>{title}</h3>
      </div>
      {displayed.length === 0 ? (
        <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>لا توجد طلبات بعد</div>
      ) : displayed.map((b, i) => (
        <div key={b.id || i} style={{
          padding: '14px 24px',
          borderBottom: '1px solid rgba(255,255,255,0.04)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          flexWrap: 'wrap', gap: 12,
        }}>
          <div>
            <div style={{ fontWeight: 600, color: '#fff', fontSize: 14 }}>{b.customer_name}</div>
            <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>{b.car_name} · {b.customer_phone}</div>
          </div>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <span style={{ fontWeight: 700, color: '#f0b429', fontSize: 15 }}>{(b.total || 0).toLocaleString()} ر.س</span>
            <span style={{
              padding: '4px 12px', borderRadius: 20, fontSize: 11, fontWeight: 600,
              background: statusMap[b.status]?.bg, color: statusMap[b.status]?.color,
              whiteSpace: 'nowrap',
            }}>
              {statusMap[b.status]?.label || b.status}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── About ────────────────────────────────────────────────────────────────────

function AboutPage() {
  return (
    <section style={{ padding: '80px 24px', maxWidth: 900, margin: '0 auto', textAlign: 'center' }}>
      <span style={{ color: '#f0b429', fontSize: 13, fontWeight: 600, letterSpacing: 2 }}>من نحن</span>
      <h2 style={{ fontSize: 'clamp(28px, 4vw, 42px)', fontWeight: 900, margin: '16px 0 20px', color: '#fff' }}>مكتب موكار لتأجير السيارات</h2>
      <p style={{ color: '#9ca3af', fontSize: 16, lineHeight: 1.8, marginBottom: 48 }}>
        نخدم عملاءنا منذ أكثر من 8 سنوات بأعلى معايير الجودة. أسطولنا يضم أحدث الموديلات مع تأمين شامل وخدمة على مدار الساعة.
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 24 }}>
        {[['🛡️', 'تأمين شامل', 'جميع سياراتنا مؤمنة تأميناً شاملاً'], ['🕐', 'خدمة 24/7', 'فريق دعم متاح على مدار الساعة'], ['🚗', 'أسطول متنوع', 'أكثر من 15 سيارة بمختلف الفئات'], ['💎', 'جودة مضمونة', 'سيارات نظيفة ومصانة دورياً']].map(([icon, title, desc]) => (
          <div key={title} className="glass-card" style={{ borderRadius: 16, padding: 28 }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>{icon}</div>
            <div style={{ fontWeight: 700, color: '#fff', marginBottom: 8 }}>{title}</div>
            <div style={{ color: '#6b7280', fontSize: 14 }}>{desc}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

// ─── Contact ──────────────────────────────────────────────────────────────────

function ContactPage() {
  const [sent, setSent] = useState(false)
  const [form, setForm] = useState({ name: '', phone: '', message: '' })

  return (
    <section style={{ padding: '80px 24px', maxWidth: 700, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <span style={{ color: '#f0b429', fontSize: 13, fontWeight: 600, letterSpacing: 2 }}>تواصل معنا</span>
        <h2 style={{ fontSize: 'clamp(28px, 4vw, 42px)', fontWeight: 900, margin: '16px 0 16px', color: '#fff' }}>نحن هنا لمساعدتك</h2>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 36 }}>
        {[['📞', 'الهاتف', '—', null], ['💬', 'واتساب', '—', null], ['📍', 'الموقع', 'اضغط للخريطة', 'https://maps.app.goo.gl/ww8eN5bpSr61xTo56']].map(([icon, l, v, href]) => (
          <div key={l} className="glass-card" style={{ borderRadius: 14, padding: 20, textAlign: 'center', cursor: href ? 'pointer' : 'default' }}
            onClick={() => href && window.open(href, '_blank')}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>{icon}</div>
            <div style={{ color: '#f0b429', fontSize: 11, fontWeight: 600, marginBottom: 4 }}>{l}</div>
            <div style={{ color: href ? '#f0b429' : '#fff', fontSize: 13, fontWeight: 600, textDecoration: href ? 'underline' : 'none' }}>{v}</div>
          </div>
        ))}
      </div>
      {sent ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
          <h3 style={{ color: '#fff', fontWeight: 700 }}>تم إرسال رسالتك!</h3>
          <p style={{ color: '#9ca3af' }}>سنتواصل معك قريباً</p>
        </div>
      ) : (
        <div className="glass-card" style={{ borderRadius: 20, padding: 32 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>الاسم</label>
              <input type="text" placeholder="اسمك الكريم" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>رقم الجوال</label>
              <input type="tel" placeholder="05XXXXXXXX" value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>الرسالة</label>
              <textarea placeholder="استفسارك أو طلبك..." value={form.message} rows={4}
                onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
                style={{ background: 'rgba(6,13,31,0.8)', border: '1px solid rgba(212,160,23,0.3)', color: 'white', borderRadius: 8, padding: '10px 14px', width: '100%', outline: 'none', resize: 'vertical', fontFamily: 'inherit' }} />
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
    <footer style={{ background: 'rgba(6,13,31,0.97)', borderTop: '1px solid rgba(212,160,23,0.15)', padding: '48px 24px 24px', marginTop: 80 }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 40, marginBottom: 40 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
              <div style={{ width: 34, height: 34, background: 'linear-gradient(135deg, #f0b429, #ffd04d)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <CarIcon size={17} color="#0b1d54" />
              </div>
              <span style={{ fontWeight: 800, color: '#fff', fontSize: 15 }}>مكتب موكار</span>
            </div>
            <p style={{ color: '#6b7280', fontSize: 13, lineHeight: 1.7 }}>أفضل تجربة تأجير سيارات بأعلى معايير الجودة.</p>
          </div>
          <div>
            <h4 style={{ color: '#f0b429', fontSize: 13, fontWeight: 700, marginBottom: 14 }}>روابط سريعة</h4>
            {[['الرئيسية', 'home'], ['معرض السيارات', 'cars'], ['عن المكتب', 'about'], ['تواصل معنا', 'contact']].map(([l, id]) => (
              <div key={id} style={{ marginBottom: 8 }}>
                <span className="nav-link" style={{ fontSize: 13 }} onClick={() => setCurrentPage(id)}>{l}</span>
              </div>
            ))}
          </div>
          <div>
            <h4 style={{ color: '#f0b429', fontSize: 13, fontWeight: 700, marginBottom: 14 }}>تواصل معنا</h4>
            <div style={{ color: '#9ca3af', fontSize: 13, lineHeight: 2.2 }}>
              <div>📞 —</div>
              <div>💬 واتساب: —</div>
              <div style={{ cursor: 'pointer' }} onClick={() => window.open('https://maps.app.goo.gl/ww8eN5bpSr61xTo56', '_blank')}>📍 موقعنا على الخريطة</div>
              <div>🕐 8 ص – 10 م</div>
            </div>
          </div>
        </div>
        <div style={{ borderTop: '1px solid rgba(212,160,23,0.1)', paddingTop: 20, textAlign: 'center', color: '#4b5563', fontSize: 12 }}>
          © 2026 مكتب موكار لتأجير السيارات · مدعوم بـ{' '}
          <span style={{ color: 'rgba(212,160,23,0.6)' }}>Supabase</span>
        </div>
      </div>
    </footer>
  )
}

// ─── App Root ─────────────────────────────────────────────────────────────────

export default function App() {
  const [currentPage, setCurrentPage] = useState('home')
  const [bookingCar, setBookingCar] = useState(null)
  const [cars, setCars] = useState(DEMO_CARS)
  const [bookings, setBookings] = useState(DEMO_BOOKINGS)
  const [loadingCars, setLoadingCars] = useState(false)
  const [session, setSession] = useState(null)
  const [authChecked, setAuthChecked] = useState(false)
  const [toast, setToast] = useState(null)
  const [searchFilter, setSearchFilter] = useState(null)
  const unsubRef = useRef(null)

  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type, key: Date.now() })
  }, [])

  const loadData = useCallback(async () => {
    if (!isConfigured) return
    setLoadingCars(true)
    try {
      const [carsData, bookingsData] = await Promise.all([fetchCars(), fetchBookings()])
      setCars(carsData)
      setBookings(bookingsData)
    } catch (err) {
      console.error('Failed to load data:', err)
      showToast('تعذّر تحميل البيانات من Supabase', 'error')
    } finally {
      setLoadingCars(false)
    }
  }, [showToast])

  // Auth listener
  useEffect(() => {
    if (!isConfigured) { setAuthChecked(true); return }
    const unsub = onAuthChange((s) => {
      setSession(s)
      setAuthChecked(true)
    })
    return unsub
  }, [])

  // Load data on mount
  useEffect(() => { loadData() }, [loadData])

  // Realtime bookings subscription (when on dashboard and authenticated)
  useEffect(() => {
    if (!isConfigured || !session) return
    unsubRef.current = subscribeToBookings((newBooking) => {
      setBookings(prev => [newBooking, ...prev])
      showToast(`حجز جديد: ${newBooking.customer_name}`, 'info')
    })
    return () => unsubRef.current?.()
  }, [session, showToast])

  const handleBookCar = useCallback((car) => setBookingCar(car), [])

  const handleConfirmBooking = useCallback(async (data) => {
    let saved
    if (isConfigured) {
      saved = await createBooking(data)
      setBookings(prev => [saved, ...prev])
      // Send WhatsApp notification (non-blocking)
      notifyWhatsApp(saved)
    } else {
      saved = {
        id: `BK${Date.now()}`, car_name: data.carName,
        customer_name: data.name, customer_phone: data.phone,
        days: data.days, total: data.total, status: 'pending',
        created_at: new Date().toISOString(),
      }
      setBookings(prev => [saved, ...prev])
    }
    showToast('✅ تم الحجز! سيصلك تأكيد على واتساب.')
  }, [showToast])

  const handleSignOut = useCallback(async () => {
    await signOut()
    setCurrentPage('home')
  }, [])

  const handleDeleteCar = useCallback(async (carId) => {
    try {
      await deleteCar(carId)
      setCars(prev => prev.filter(c => c.id !== carId))
      showToast('✅ تم حذف السيارة')
    } catch {
      showToast('❌ فشل الحذف', 'error')
    }
  }, [showToast])

  const pendingCount = bookings.filter(b => b.status === 'pending').length

  return (
    <div style={{ minHeight: '100vh', background: '#0b1d54' }}>
      {!isConfigured && <ConfigBanner />}
      <Navbar currentPage={currentPage} setCurrentPage={setCurrentPage} pendingCount={pendingCount} session={session} />

      {currentPage === 'home' && (
        <>
          <HeroSection onSearch={setSearchFilter} setCurrentPage={setCurrentPage} />
          <CarGallery searchFilter={searchFilter} onBookCar={handleBookCar} cars={cars} loading={loadingCars} />
        </>
      )}
      {currentPage === 'cars' && (
        <CarGallery searchFilter={searchFilter} onBookCar={handleBookCar} cars={cars} loading={loadingCars} />
      )}
      {currentPage === 'about'   && <AboutPage />}
      {currentPage === 'contact' && <ContactPage />}
      {currentPage === 'dashboard' && (
        !authChecked ? (
          <div style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f0b429' }}>جاري التحقق...</div>
        ) : (!isConfigured || session) ? (
          <Dashboard
            session={session}
            bookings={bookings}
            cars={cars}
            onSignOut={handleSignOut}
            onRefresh={loadData}
            onDeleteCar={handleDeleteCar}
            loading={loadingCars}
          />
        ) : (
          <AdminLogin onLogin={() => setCurrentPage('dashboard')} />
        )
      )}

      <Footer setCurrentPage={setCurrentPage} />

      {bookingCar && (
        <BookingModal
          car={bookingCar}
          onClose={() => setBookingCar(null)}
          onConfirm={async (data) => {
            await handleConfirmBooking(data)
            setBookingCar(null)
          }}
        />
      )}

      {toast && (
        <Toast key={toast.key} message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
    </div>
  )
}
