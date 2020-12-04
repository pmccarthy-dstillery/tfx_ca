with labeled as (
    select deviceid, 
    devicetype, 
    case when regexp_contains(content,"{{inputs.parameters.seed_pattern}}") then 1 else 0 end as label,
    content
  from tfx_ca.visitdata
), 
positives as (
  select deviceid,
    devicetype,
    label,
    content    
  from labeled
  where label = 1
  limit 100000
),
negatives as (
  select deviceid,
    devicetype,
    label,
    content
  from labeled
  where label = 0
  limit 900000
),

positives_ranked as (
  select label,
  content,
  (rank() over(order by rand()))*9+.5 as rnk
  from positives
),

negatives_ranked as (
  select label,
  content,
  (rank() over(order by rand())) as rnk
  from negatives
)

select label, content, rnk from 
(select label, content, rnk 
from positives_ranked) 

union all 

(select label, content, rnk 
from negatives_ranked)
order by rnk