-- ── حذف جميع الحجوزات والسيارات القديمة ────────────────────────
DELETE FROM public.bookings;
DELETE FROM public.cars;

-- ── إعادة رفع السيارات باسم موكار ──────────────────────────────
INSERT INTO public.cars (name, type, type_label, price, seats, year, fuel, transmission, available, color, features, image_url) VALUES
  ('تويوتا كامري',      'sedan',  'سيدان',  150, 5, 2024, 'بنزين', 'أوتوماتيك', true,  '#1a3a6b', ARRAY['بلوتوث','كاميرا خلفية','تحكم بالمحرك'],        'https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb'),
  ('BMW الفئة الخامسة', 'sedan',  'سيدان',  350, 5, 2024, 'بنزين', 'أوتوماتيك', true,  '#0a0a0a', ARRAY['جلد فاخر','نظام ملاحة','سقف بانورامي'],        'https://images.unsplash.com/photo-1555215695-3004980ad54e'),
  ('هيونداي توسان',     'suv',    'SUV',    200, 5, 2023, 'بنزين', 'أوتوماتيك', true,  '#2d4a1e', ARRAY['دفع رباعي','شاشة لمس','تحذير مسار'],           'https://images.unsplash.com/photo-1625047509252-ab38fb5c7343'),
  ('تويوتا لاند كروزر', 'suv',    'SUV',    500, 7, 2024, 'بنزين', 'أوتوماتيك', true,  '#1a1a2e', ARRAY['7 مقاعد','دفع رباعي','نظام تعليق هوائي'],      'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b'),
  ('كيا بيكانتو',       'economy','اقتصادي', 80, 4, 2023, 'بنزين', 'أوتوماتيك', true,  '#8b0000', ARRAY['توفير الوقود','مريح للمدينة','سهل الركن'],      'https://images.unsplash.com/photo-1541899481282-d53bffe3c35d'),
  ('هيونداي إيلانترا',  'sedan',  'سيدان',  120, 5, 2023, 'بنزين', 'أوتوماتيك', true,  '#1e3a5f', ARRAY['شاشة 10 بوصة','بلوتوث','كاميرا أمامية وخلفية'],'https://images.unsplash.com/photo-1494976388531-d1058494cdd8');
