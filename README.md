# tfx_ca
Build Crafted Audiences in a semi-prod way on TFX/GC

To run locally:

    python -m tfx_ca -p local

Or on KFP:

    python -m tfx_ca -p kfp


To use the Cloud AI service with the kfp runner instead of running on our k8s cluster, comment out 

    ai_platform_training_args = None # <--- this makes the difference between running on k8s hardware and ml api

in `__main__.py`.


