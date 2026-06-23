-- ============================================================
-- مكتب الهدى لتأجير السيارات - Supabase Schema
-- Run this in the Supabase SQL Editor to set up your database
-- ============================================================

-- ── Enable UUID extension ────────────────────────────────────
create extension if not exists "uuid-ossp";

-- ── Cars table ───────────────────────────────────────────────
create table public.cars (
  id          uuid primary key default uuid_generate_v4(),
  name        text not null,
  type        text not null check (type in ('sedan', 'suv', 'economy')),
  type_label  text not null,
  price       integer not null,
  seats       integer not null default 5,
  year        integer not null,
  fuel        text not null default 'بنزين',
  transmission text not null default 'أوتوماتيك',
  available   boolean not null default true,
  color       text not null default '#1a3a6b',
  features    text[] not null default '{}',
  created_at  timestamptz default now()
);

-- ── Bookings table ───────────────────────────────────────────
create table public.bookings (
  id             uuid primary key default uuid_generate_v4(),
  car_id         uuid references public.cars(id) on delete set null,
  car_name       text not null,
  customer_name  text not null,
  customer_phone text not null,
  id_number      text not null,
  license_number text not null,
  pickup_date    date not null,
  dropoff_date   date not null,
  days           integer not null,
  price_per_day  integer not null,
  total          integer not null,
  status         text not null default 'pending' check (status in ('pending', 'active', 'completed', 'cancelled')),
  notes          text,
  created_at     timestamptz default now()
);

-- ── Row Level Security ────────────────────────────────────────
alter table public.cars    enable row level security;
alter table public.bookings enable row level security;

-- Cars: anyone can read (for the public website)
create policy "Cars are viewable by everyone"
  on public.cars for select using (true);

-- Cars: only authenticated users (admin) can modify
create policy "Admin can manage cars"
  on public.cars for all using (auth.role() = 'authenticated');

-- Bookings: anyone can insert (customers booking)
create policy "Anyone can create a booking"
  on public.bookings for insert with check (true);

-- Bookings: only authenticated users (admin) can read/update all bookings
create policy "Admin can view all bookings"
  on public.bookings for select using (auth.role() = 'authenticated');

create policy "Admin can update bookings"
  on public.bookings for update using (auth.role() = 'authenticated');

-- ── Seed initial car data ─────────────────────────────────────
insert into public.cars (name, type, type_label, price, seats, year, fuel, transmission, available, color, features) values
  ('تويوتا كامري',    'sedan',   'سيدان',       150, 5, 2024, 'بنزين', 'أوتوماتيك', true,  '#1a3a6b', ARRAY['بلوتوث', 'كاميرا خلفية', 'تحكم بالمحرك']),
  ('BMW الفئة الخامسة','sedan',  'سيدان',       380, 5, 2024, 'بنزين', 'أوتوماتيك', true,  '#2a1a4a', ARRAY['شاشة لمس', 'تحكم بالصوت', 'مقاعد جلد', 'نظام ملاحة']),
  ('هيونداي توسان',   'suv',    'دفع رباعي',   200, 5, 2023, 'بنزين', 'أوتوماتيك', true,  '#1a4a2a', ARRAY['دفع رباعي', 'فتحة سقف', 'كاميرا 360']),
  ('تويوتا لاند كروزر','suv',   'دفع رباعي',   550, 7, 2024, 'ديزل',  'أوتوماتيك', false, '#3a1a1a', ARRAY['7 مقاعد', 'دفع رباعي', 'شاشة 12"', 'مقاعد مدفأة']),
  ('كيا بيكانتو',     'economy','اقتصادية',     80, 5, 2023, 'بنزين', 'أوتوماتيك', true,  '#1a3a3a', ARRAY['اقتصادي بالوقود', 'سهل القيادة', 'موقف سهل']),
  ('هيونداي إيلانترا','economy','اقتصادية',    110, 5, 2024, 'بنزين', 'أوتوماتيك', true,  '#1a2a4a', ARRAY['بلوتوث', 'شاشة لمس', 'USB']);

-- ── Seed sample bookings ──────────────────────────────────────
insert into public.bookings (car_name, customer_name, customer_phone, id_number, license_number, pickup_date, dropoff_date, days, price_per_day, total, status)
values
  ('تويوتا لاند كروزر', 'أحمد محمد السعيد',   '0501234567', '1234567890', 'DL123456', '2026-06-20', '2026-06-23', 3, 550, 1650, 'active'),
  ('BMW الفئة الخامسة',  'سارة عبدالله الأحمد', '0559876543', '9876543210', 'DL789012', '2026-06-22', '2026-06-27', 5, 380, 1900, 'pending'),
  ('هيونداي توسان',     'محمد علي الزهراني',   '0531112233', '1122334455', 'DL345678', '2026-06-18', '2026-06-20', 2, 200, 400,  'completed');
