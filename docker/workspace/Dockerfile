FROM jupyter/scipy-notebook:latest

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

# welcome notebook
COPY workspace/welcome.ipynb /home/jovyan/work/

USER jovyan

WORKDIR /workspace
