with src as (
  select
    transaction_id,
    user_id,
    amount,
    currency,
    label as label_raw,
    booking_date,
    created_at,
    category as category_true,
    source_file
  from {{ source('raw', 'raw_transactions') }}
),

normalized as (
  select
    *,
    -- Normalisation “merchant”: uppercase, suppression ponctuation, compactage espaces
    regexp_replace(upper(label_raw), '[^A-Z0-9 ]', ' ') as label_alnum,
    regexp_replace(regexp_replace(upper(label_raw), '[^A-Z0-9 ]', ' '), '\s+', ' ') as label_norm,
    -- heuristique: merchant = premier token ou 2 tokens si “E LECLERC”, “AIR FRANCE”
    case
      when regexp_matches(label_norm, '^(E LECLERC)') then 'E LECLERC'
      when regexp_matches(label_norm, '^(AIR FRANCE|AIRFRANCE)') then 'AIR FRANCE'
      when regexp_matches(label_norm, '^(CB )') then split_part(label_norm, ' ', 2)
      when regexp_matches(label_norm, '^(VIR )') then split_part(label_norm, ' ', 2)
      when regexp_matches(label_norm, '^(PRELEV )') then split_part(label_norm, ' ', 2)
      else split_part(label_norm, ' ', 1)
    end as merchant_guess
  from src
)

select
  transaction_id,
  user_id,
  amount,
  currency,
  booking_date,
  created_at,
  source_file,
  category_true,
  label_raw,
  label_norm,
  merchant_guess
from normalized
