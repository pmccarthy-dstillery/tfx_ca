FROM tensorflow/tfx:0.25.0
RUN mkdir -p /dstillery/tfx_ca
COPY tfx_ca /dstillery/tfx_ca/
ENV PYTHONPATH="/dstillery:${PYTHONPATH}"