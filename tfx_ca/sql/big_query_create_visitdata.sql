 CREATE TABLE 
   tfx_ca.visitdata (
       deviceid STRING OPTIONS(description="Device best device ID"),
       devicetype STRING OPTIONS(description="Device best device ID type"),
       content STRING OPTIONS(description="A space-separated list of base36-encoded content"),
       hit_date DATE OPTIONS(description="Date of record ET")
   )
 PARTITION BY
   hit_date
 OPTIONS 
   (
       partition_expiration_days=3,
       description="Visitdata for training Crafted Audiences"
   )