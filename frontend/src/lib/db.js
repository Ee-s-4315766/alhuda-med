import { supabase } from './supabase'

// ── Cars ──────────────────────────────────────────────────────

export async function fetchCars() {
  const { data, error } = await supabase
    .from('cars')
    .select('*')
    .order('price', { ascending: true })
  if (error) throw error
  return data
}

export async function deleteCar(carId) {
  const { error } = await supabase
    .from('cars')
    .delete()
    .eq('id', carId)
  if (error) throw error
}

export async function updateCar(carId, fields) {
  const { data, error } = await supabase
    .from('cars')
    .update(fields)
    .eq('id', carId)
    .select()
    .single()
  if (error) throw error
  return data
}

export async function updateCarAvailability(carId, available) {
  const { error } = await supabase
    .from('cars')
    .update({ available })
    .eq('id', carId)
  if (error) throw error
}

// ── Bookings ──────────────────────────────────────────────────

export async function createBooking(booking) {
  const { data, error } = await supabase
    .from('bookings')
    .insert([{
      car_id:          booking.carId,
      car_name:        booking.carName,
      customer_name:   booking.name,
      customer_phone:  booking.phone,
      id_number:       booking.idNumber,
      license_number:  booking.licenseNumber,
      pickup_date:     booking.pickup,
      dropoff_date:    booking.dropoff,
      days:            booking.days,
      price_per_day:   booking.pricePerDay,
      total:           booking.total,
      status:          'pending',
    }])
    .select()
    .single()
  if (error) throw error
  return data
}

export async function fetchBookings() {
  const { data, error } = await supabase
    .from('bookings')
    .select('*')
    .order('created_at', { ascending: false })
  if (error) throw error
  return data
}

export async function updateBookingStatus(bookingId, status) {
  const { error } = await supabase
    .from('bookings')
    .update({ status })
    .eq('id', bookingId)
  if (error) throw error
}

// ── Realtime subscriptions ────────────────────────────────────

export function subscribeToBookings(onNewBooking) {
  const channel = supabase
    .channel('bookings-changes')
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'bookings' },
      (payload) => onNewBooking(payload.new)
    )
    .subscribe()
  return () => supabase.removeChannel(channel)
}

// ── Auth ──────────────────────────────────────────────────────

export async function signIn(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password })
  if (error) throw error
  return data
}

export async function signOut() {
  const { error } = await supabase.auth.signOut()
  if (error) throw error
}

export async function getSession() {
  const { data: { session } } = await supabase.auth.getSession()
  return session
}

export function onAuthChange(callback) {
  const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
    callback(session)
  })
  return () => subscription.unsubscribe()
}

// ── WhatsApp notification (via Supabase Edge Function) ────────

export async function notifyWhatsApp(booking) {
  try {
    const { error } = await supabase.functions.invoke('send-whatsapp', {
      body: { booking },
    })
    if (error) console.warn('WhatsApp notification failed:', error.message)
  } catch (err) {
    console.warn('WhatsApp notification error:', err.message)
    // Never block booking on notification failure
  }
}

// ── Dashboard stats ───────────────────────────────────────────

export async function fetchDashboardStats() {
  const [carsRes, bookingsRes] = await Promise.all([
    supabase.from('cars').select('id, available'),
    supabase.from('bookings').select('id, status, total, created_at'),
  ])
  if (carsRes.error) throw carsRes.error
  if (bookingsRes.error) throw bookingsRes.error

  const cars     = carsRes.data
  const bookings = bookingsRes.data

  return {
    totalCars:     cars.length,
    availableCars: cars.filter(c => c.available).length,
    rentedCars:    cars.filter(c => !c.available).length,
    totalBookings: bookings.length,
    pendingCount:  bookings.filter(b => b.status === 'pending').length,
    activeCount:   bookings.filter(b => b.status === 'active').length,
    totalRevenue:  bookings
      .filter(b => b.status !== 'cancelled')
      .reduce((sum, b) => sum + (b.total || 0), 0),
  }
}
