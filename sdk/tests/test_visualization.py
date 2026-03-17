'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for visualization context module
'''

import pytest
from unittest.mock import MagicMock
from openuba.visualization import VisualizationContext


class TestVisualizationContext:
    '''test VisualizationContext rendering and detection methods'''

    # ─── Backend Output Map ─────────────────────────────────────────

    def test_backend_output_map_matplotlib(self):
        '''test matplotlib maps to svg'''
        assert VisualizationContext.BACKEND_OUTPUT_MAP["matplotlib"] == "svg"

    def test_backend_output_map_plotly(self):
        '''test plotly maps to plotly'''
        assert VisualizationContext.BACKEND_OUTPUT_MAP["plotly"] == "plotly"

    def test_backend_output_map_bokeh(self):
        '''test bokeh maps to bokeh'''
        assert VisualizationContext.BACKEND_OUTPUT_MAP["bokeh"] == "bokeh"

    def test_backend_output_map_altair(self):
        '''test altair maps to vega-lite'''
        assert VisualizationContext.BACKEND_OUTPUT_MAP["altair"] == "vega-lite"

    def test_backend_output_map_seaborn(self):
        '''test seaborn maps to svg'''
        assert VisualizationContext.BACKEND_OUTPUT_MAP["seaborn"] == "svg"

    def test_backend_output_map_datashader(self):
        '''test datashader maps to png'''
        assert VisualizationContext.BACKEND_OUTPUT_MAP["datashader"] == "png"

    def test_backend_output_map_networkx(self):
        '''test networkx maps to svg'''
        assert VisualizationContext.BACKEND_OUTPUT_MAP["networkx"] == "svg"

    def test_backend_output_map_geopandas(self):
        '''test geopandas maps to svg'''
        assert VisualizationContext.BACKEND_OUTPUT_MAP["geopandas"] == "svg"

    def test_backend_output_map_plotnine(self):
        '''test plotnine maps to svg'''
        assert VisualizationContext.BACKEND_OUTPUT_MAP["plotnine"] == "svg"

    # ─── Backend Detection ──────────────────────────────────────────

    def test_detect_backend_matplotlib(self):
        '''test detecting matplotlib figure'''
        figure = MagicMock()
        figure.__class__.__module__ = 'matplotlib.figure'
        result = VisualizationContext._detect_backend(figure)
        assert result == 'matplotlib'

    def test_detect_backend_plotly(self):
        '''test detecting plotly figure'''
        figure = MagicMock()
        figure.__class__.__module__ = 'plotly.graph_objs._figure'
        result = VisualizationContext._detect_backend(figure)
        assert result == 'plotly'

    def test_detect_backend_bokeh(self):
        '''test detecting bokeh figure'''
        figure = MagicMock()
        figure.__class__.__module__ = 'bokeh.plotting.figure'
        result = VisualizationContext._detect_backend(figure)
        assert result == 'bokeh'

    def test_detect_backend_altair(self):
        '''test detecting altair chart'''
        figure = MagicMock()
        figure.__class__.__module__ = 'altair.vegalite.v5.api'
        result = VisualizationContext._detect_backend(figure)
        assert result == 'altair'

    def test_detect_backend_plotnine(self):
        '''test detecting plotnine figure'''
        figure = MagicMock()
        figure.__class__.__module__ = 'plotnine.ggplot'
        result = VisualizationContext._detect_backend(figure)
        assert result == 'plotnine'

    def test_detect_backend_networkx(self):
        '''test detecting networkx graph'''
        figure = MagicMock()
        figure.__class__.__module__ = 'networkx.classes.graph'
        result = VisualizationContext._detect_backend(figure)
        assert result == 'networkx'

    def test_detect_backend_unknown_defaults_to_matplotlib(self):
        '''test that unknown backend defaults to matplotlib'''
        figure = MagicMock()
        figure.__class__.__module__ = 'custom.unknown.module'
        result = VisualizationContext._detect_backend(figure)
        assert result == 'matplotlib'

    # ─── Render with Explicit Backend ───────────────────────────────

    def test_render_matplotlib(self):
        '''test rendering a matplotlib figure'''
        figure = MagicMock()
        figure.__class__.__module__ = 'matplotlib.figure'

        def mock_savefig(buf, format=None, bbox_inches=None):
            buf.write(b'<svg>test</svg>')

        figure.savefig = mock_savefig
        result = VisualizationContext.render(figure, backend="matplotlib", format="svg")
        assert '<svg>test</svg>' in result

    def test_render_matplotlib_png(self):
        '''test rendering matplotlib figure as png returns base64'''
        import base64
        figure = MagicMock()
        figure.__class__.__module__ = 'matplotlib.figure'

        def mock_savefig(buf, format=None, bbox_inches=None):
            buf.write(b'\x89PNG\r\n')

        figure.savefig = mock_savefig
        result = VisualizationContext.render(figure, backend="matplotlib", format="png")
        # should be base64 encoded
        base64.b64decode(result)  # should not raise

    def test_render_seaborn(self):
        '''test rendering a seaborn figure (delegates to matplotlib)'''
        figure = MagicMock()
        figure.__class__.__module__ = 'seaborn.axisgrid'
        mock_fig = MagicMock()

        def mock_savefig(buf, format=None, bbox_inches=None):
            buf.write(b'<svg>seaborn</svg>')

        mock_fig.savefig = mock_savefig
        figure.get_figure.return_value = mock_fig
        result = VisualizationContext.render(figure, backend="seaborn", format="svg")
        assert '<svg>seaborn</svg>' in result

    def test_render_plotly(self):
        '''test rendering a plotly figure'''
        figure = MagicMock()
        figure.__class__.__module__ = 'plotly.graph_objs._figure'
        figure.to_json.return_value = '{"data": [], "layout": {}}'
        result = VisualizationContext.render(figure, backend="plotly")
        assert '"data"' in result

    def test_render_altair(self):
        '''test rendering an altair chart'''
        figure = MagicMock()
        figure.__class__.__module__ = 'altair.vegalite.v5.api'
        figure.to_json.return_value = '{"$schema": "vega-lite"}'
        result = VisualizationContext.render(figure, backend="altair")
        assert '"$schema"' in result

    def test_render_unsupported_backend(self):
        '''test that unsupported backend raises ValueError'''
        figure = MagicMock()
        with pytest.raises(ValueError, match="unsupported backend"):
            VisualizationContext.render(figure, backend="unsupported_lib")

    # ─── Render with Auto-Detection ─────────────────────────────────

    def test_render_auto_detect_matplotlib(self):
        '''test rendering with auto-detected matplotlib backend'''
        figure = MagicMock()
        figure.__class__.__module__ = 'matplotlib.figure'

        def mock_savefig(buf, format=None, bbox_inches=None):
            buf.write(b'<svg>auto-detected</svg>')

        figure.savefig = mock_savefig
        result = VisualizationContext.render(figure)
        assert '<svg>auto-detected</svg>' in result

    def test_render_auto_detect_plotly(self):
        '''test rendering with auto-detected plotly backend'''
        figure = MagicMock()
        figure.__class__.__module__ = 'plotly.graph_objs._figure'
        figure.to_json.return_value = '{"auto": true}'
        result = VisualizationContext.render(figure)
        assert '"auto"' in result
