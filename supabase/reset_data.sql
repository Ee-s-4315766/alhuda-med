-- ── حذف جميع الحجوزات والسيارات القديمة ────────────────────────
DELETE FROM public.bookings;
DELETE FROM public.cars;

-- ── إعادة رفع السيارات بصور موكار الحقيقية ──────────────────────────────
INSERT INTO public.cars (name, type, type_label, price, seats, year, fuel, transmission, available, color, features, image_url) VALUES
  ('سيارة 1', 'sedan', 'سيدان', 0, 5, 2024, 'بنزين', 'أوتوماتيك', true, '#1a3a6b', ARRAY['بلوتوث'], 'https://ldirmswbmnpdjskmrgik.supabase.co/storage/v1/object/public/Cars/WhatsApp%20Image%202026-06-25%20at%2012.45.47%20PM%20(1).jpeg'),
  ('سيارة 2', 'sedan', 'سيدان', 0, 5, 2024, 'بنزين', 'أوتوماتيك', true, '#1a3a6b', ARRAY['بلوتوث'], 'https://ldirmswbmnpdjskmrgik.supabase.co/storage/v1/object/public/Cars/WhatsApp%20Image%202026-06-25%20at%2012.45.47%20PM%20(2).jpeg'),
  ('سيارة 3', 'sedan', 'سيدان', 0, 5, 2024, 'بنزين', 'أوتوماتيك', true, '#1a3a6b', ARRAY['بلوتوث'], 'https://ldirmswbmnpdjskmrgik.supabase.co/storage/v1/object/public/Cars/WhatsApp%20Image%202026-06-25%20at%2012.45.47%20PM.jpeg'),
  ('سيارة 4', 'sedan', 'سيدان', 0, 5, 2024, 'بنزين', 'أوتوماتيك', true, '#1a3a6b', ARRAY['بلوتوث'], 'https://ldirmswbmnpdjskmrgik.supabase.co/storage/v1/object/public/Cars/WhatsApp%20Image%202026-06-25%20at%2012.45.48%20PM%20(1).jpeg'),
  ('سيارة 5', 'sedan', 'سيدان', 0, 5, 2024, 'بنزين', 'أوتوماتيك', true, '#1a3a6b', ARRAY['بلوتوث'], 'https://ldirmswbmnpdjskmrgik.supabase.co/storage/v1/object/public/Cars/WhatsApp%20Image%202026-06-25%20at%2012.45.48%20PM%20(2).jpeg'),
  ('سيارة 6', 'sedan', 'سيدان', 0, 5, 2024, 'بنزين', 'أوتوماتيك', true, '#1a3a6b', ARRAY['بلوتوث'], 'https://ldirmswbmnpdjskmrgik.supabase.co/storage/v1/object/public/Cars/WhatsApp%20Image%202026-06-25%20at%2012.45.48%20PM.jpeg');
