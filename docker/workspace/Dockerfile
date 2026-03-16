FROM jupyter/scipy-notebook:python-3.11

USER root

# install openuba SDK
COPY sdk/src/openuba /tmp/openuba-sdk/src/openuba
COPY sdk/pyproject.toml /tmp/openuba-sdk/
COPY sdk/README.md /tmp/openuba-sdk/
RUN pip install --no-cache-dir /tmp/openuba-sdk/ && rm -rf /tmp/openuba-sdk

# install visualization libraries
RUN pip install --no-cache-dir \
    matplotlib \
    seaborn \
    plotly \
    bokeh \
    altair \
    plotnine \
    datashader \
    networkx \
    geopandas

# install ML frameworks
RUN pip install --no-cache-dir \
    scikit-learn \
    torch --index-url https://download.pytorch.org/whl/cpu

# install data connectors
RUN pip install --no-cache-dir \
    pyspark \
    elasticsearch \
    psycopg2-binary \
    requests \
    pandas \
    numpy

# configure JupyterLab for iframe embedding (token-less, XSRF-disabled, CSP-allowed)
# this allows the OpenUBA frontend to embed JupyterLab seamlessly in an iframe
# SECURITY: this is for local development only. For production, use per-workspace
# tokens (via OPENUBA_TOKEN / K8s Secret), restrict allow_origin to the frontend
# origin, and keep XSRF enabled.
# NOTE: we append to the base image config AND write a user-level config to ensure
# our settings take effect regardless of base image entrypoint behavior
RUN cat >> /etc/jupyter/jupyter_server_config.py << 'JCONF'

# OpenUBA iframe embedding configuration
c.ServerApp.token = ''
c.ServerApp.password = ''
c.ServerApp.allow_origin = '*'
c.ServerApp.allow_remote_access = True
c.ServerApp.disable_check_xsrf = True
c.ServerApp.tornado_settings = {
    'headers': {
        'Content-Security-Policy': "frame-ancestors * 'self'",
        'X-Frame-Options': 'ALLOWALL',
    }
}
c.NotebookApp.token = ''
c.NotebookApp.password = ''
JCONF
# also write user-level config (takes highest priority)
RUN mkdir -p /home/jovyan/.jupyter && cp /etc/jupyter/jupyter_server_config.py /home/jovyan/.jupyter/jupyter_server_config.py

# set dark theme as default
RUN mkdir -p /opt/conda/share/jupyter/lab/settings && \
    echo '{"@jupyterlab/apputils-extension:themes": {"theme": "JupyterLab Dark"}}' \
    > /opt/conda/share/jupyter/lab/settings/overrides.json

# workspace notebooks (welcome + SDK tutorials)
COPY workspace/*.ipynb /home/jovyan/work/
RUN chown -R 1000:100 /home/jovyan/work/

USER jovyan

WORKDIR /home/jovyan/work
