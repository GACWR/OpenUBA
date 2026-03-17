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
        returns the rendered content as a string (SVG, JSON, or base64 PNG)
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
        try:
            import matplotlib.figure
            if isinstance(figure, matplotlib.figure.Figure):
                return 'matplotlib'
        except ImportError:
            pass

        type_name = type(figure).__module__

        if 'matplotlib' in type_name:
            return 'matplotlib'
        elif 'seaborn' in type_name:
            return 'seaborn'
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
        elif 'datashader' in type_name:
            return 'datashader'
        elif 'geopandas' in type_name:
            return 'geopandas'

        # check for matplotlib Axes (returned by both matplotlib and seaborn)
        try:
            import matplotlib.axes
            if isinstance(figure, matplotlib.axes.Axes):
                return 'seaborn'
        except ImportError:
            pass

        # check for geopandas GeoDataFrame
        if hasattr(figure, 'geometry') and hasattr(figure, 'plot'):
            return 'geopandas'

        # check for datashader Image
        if hasattr(figure, 'to_pil'):
            return 'datashader'

        raise TypeError(
            f"cannot detect backend for {type(figure).__name__}. "
            f"supported backends: {list(VisualizationContext.BACKEND_OUTPUT_MAP.keys())}"
        )

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
        import json
        from bokeh.embed import json_item
        return json.dumps(json_item(figure))

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
        '''render geopandas GeoDataFrame or pre-rendered matplotlib Figure'''
        import matplotlib.figure
        if isinstance(figure, matplotlib.figure.Figure):
            return VisualizationContext._render_matplotlib(figure, format)
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(12, 8))
        figure.plot(ax=ax)
        return VisualizationContext._render_matplotlib(fig, format)


def render(figure, backend=None, viz_id=None, _client=None):
    '''
    render a figure and optionally push to the platform.
    following the OMS pattern: render failures are fatal, push failures are silent.

    Args:
        figure: matplotlib Figure, seaborn axes, plotly Figure, etc.
        backend: override auto-detection (matplotlib, seaborn, plotly, etc.)
        viz_id: if provided, auto-push rendered output to the platform
        _client: optional client override (for testing)

    Returns:
        dict with {"type": "svg|plotly|bokeh|...", "content": "..."}
    '''
    if backend is None:
        backend = VisualizationContext._detect_backend(figure)

    output_type = VisualizationContext.BACKEND_OUTPUT_MAP.get(backend, "svg")
    content = VisualizationContext.render(figure, backend=backend)

    # auto-push to platform when viz_id is provided
    if viz_id:
        if _client is None:
            from openuba import _get_client
            _client = _get_client()
        try:
            _client.update_visualization(str(viz_id), rendered_output=content)
        except Exception as e:
            # push failures are silent — don't break the render
            logger.debug(f"failed to push rendered output for {viz_id}: {e}")

    return {"type": output_type, "content": content}
