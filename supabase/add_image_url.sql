-- ── Add image_url column to cars ─────────────────────────────
ALTER TABLE public.cars ADD COLUMN IF NOT EXISTS image_url text;

-- ── Update each car with a real Unsplash photo ────────────────
UPDATE public.cars SET image_url = 'https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb'
  WHERE name = 'تويوتا كامري';

UPDATE public.cars SET image_url = 'https://images.unsplash.com/photo-1555215695-3004980ad54e'
  WHERE name = 'BMW الفئة الخامسة';

UPDATE public.cars SET image_url = 'https://images.unsplash.com/photo-1625047509252-ab38fb5c7343'
  WHERE name = 'هيونداي توسان';

UPDATE public.cars SET image_url = 'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b'
  WHERE name = 'تويوتا لاند كروزر';

UPDATE public.cars SET image_url = 'https://images.unsplash.com/photo-1541899481282-d53bffe3c35d'
  WHERE name = 'كيا بيكانتو';

UPDATE public.cars SET image_url = 'https://images.unsplash.com/photo-1494976388531-d1058494cdd8'
  WHERE name = 'هيونداي إيلانترا';
