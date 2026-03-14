'''
Copyright 2019-Present The OpenUBA Platform Authors
visualization module for multi-backend rendering
'''

import io
import base64
import logging

logger = logging.getLogger(__name__)


class VisualizationContext:
    '''
    context for rendering visualizations across multiple backends
    supports: matplotlib, seaborn, plotly, bokeh, altair, plotnine,
              datashader, networkx, geopandas
    '''

    BACKEND_OUTPUT_MAP = {
        "matplotlib": "svg",
        "seaborn": "svg",
        "plotly": "plotly",
        "bokeh": "bokeh",
        "altair": "vega-lite",
        "plotnine": "svg",
        "datashader": "png",
        "networkx": "svg",
        "geopandas": "svg",
    }

    @staticmethod
    def render(figure, backend=None, format=None):
        '''
        render a figure to string output
        auto-detects backend from figure type if not specified
        '''
        if backend is None:
            backend = VisualizationContext._detect_backend(figure)

        if format is None:
            format = VisualizationContext.BACKEND_OUTPUT_MAP.get(backend, "svg")

        renderer = getattr(VisualizationContext, f"_render_{backend}", None)
        if renderer is None:
            raise ValueError(f"unsupported backend: {backend}")

        return renderer(figure, format)

    @staticmethod
    def _detect_backend(figure):
        '''detect rendering backend from figure type'''
        type_name = type(figure).__module__

        if 'matplotlib' in type_name:
            return 'matplotlib'
        elif 'plotly' in type_name:
            return 'plotly'
        elif 'bokeh' in type_name:
            return 'bokeh'
        elif 'altair' in type_name:
            return 'altair'
        elif 'plotnine' in type_name:
            return 'plotnine'
        elif 'networkx' in type_name:
            return 'networkx'

        return 'matplotlib'

    @staticmethod
    def _render_matplotlib(figure, format="svg"):
        '''render matplotlib figure'''
        buf = io.BytesIO()
        figure.savefig(buf, format=format, bbox_inches='tight')
        buf.seek(0)
        if format == "svg":
            return buf.getvalue().decode('utf-8')
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    @staticmethod
    def _render_seaborn(figure, format="svg"):
        '''render seaborn figure (uses matplotlib backend)'''
        fig = figure.get_figure() if hasattr(figure, 'get_figure') else figure
        return VisualizationContext._render_matplotlib(fig, format)

    @staticmethod
    def _render_plotly(figure, format="plotly"):
        '''render plotly figure to JSON'''
        return figure.to_json()

    @staticmethod
    def _render_bokeh(figure, format="bokeh"):
        '''render bokeh figure to JSON'''
        from bokeh.embed import json_item
        return str(json_item(figure))

    @staticmethod
    def _render_altair(figure, format="vega-lite"):
        '''render altair chart to vega-lite JSON'''
        return figure.to_json()

    @staticmethod
    def _render_plotnine(figure, format="svg"):
        '''render plotnine figure'''
        buf = io.BytesIO()
        figure.save(buf, format=format)
        buf.seek(0)
        if format == "svg":
            return buf.getvalue().decode('utf-8')
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    @staticmethod
    def _render_datashader(figure, format="png"):
        '''render datashader image'''
        buf = io.BytesIO()
        from datashader.transfer_functions import shade
        img = figure if hasattr(figure, 'to_pil') else shade(figure)
        img.to_pil().save(buf, format='PNG')
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    @staticmethod
    def _render_networkx(figure, format="svg"):
        '''render networkx graph using matplotlib'''
        import matplotlib.pyplot as plt
        import networkx as nx
        fig, ax = plt.subplots(figsize=(10, 8))
        nx.draw(figure, ax=ax, with_labels=True, node_color='lightblue',
                node_size=500, font_size=8, arrows=True)
        return VisualizationContext._render_matplotlib(fig, format)

    @staticmethod
    def _render_geopandas(figure, format="svg"):
        '''render geopandas GeoDataFrame'''
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(12, 8))
        figure.plot(ax=ax)
        return VisualizationContext._render_matplotlib(fig, format)
