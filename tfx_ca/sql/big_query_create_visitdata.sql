 CREATE TABLE 
   TABLENAME (
       deviceid STRING OPTIONS(description="Device best device ID"),
       devicetype STRING OPTIONS(description="Device best device ID type"),
       content STRING OPTIONS(description="A comma-separated list of base36-encoded content"),
       hit_date DATE OPTIONS(description="Date of record ET")
   )
 PARTITION BY
   hit_date
 OPTIONS 
   (
       partition_expiration_days=10,
       description="Visitdata for training Crafted Audiences"
   )