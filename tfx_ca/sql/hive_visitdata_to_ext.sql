insert overwrite directory 'STAGING_DIR'
row format delimited
fields terminated by ','

select device_id, 
  device_id_type, 
  concat_ws(' ', map_keys(visits_by_site[27])),
  from_unixtime(unix_timestamp(cast(snap_date as string),'yyyyMMdd'),'yyyy-MM-dd')
  from di_device_behavior_metrics.device_data
  where snap_date=SNAP_DATE
    and device_id_type_category='DISPLAY'
    and visits_by_site[27] is not null