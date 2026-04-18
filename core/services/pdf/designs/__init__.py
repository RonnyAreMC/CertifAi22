"""Registry of PDF design strategies.

To add a new design: create `designs/<name>.py` with a
`draw_<name>_wow(c, certificado, width, height, pri, sec, ter, txt)`
function and register it below.
"""
from .classic import draw_classic_wow
from .modern import draw_modern_wow
from .geometric import draw_geometric_wow

DESIGN_REGISTRY = {
    'clasico': draw_classic_wow,
    'moderno': draw_modern_wow,
    'geometrico': draw_geometric_wow,
}

def get_design(plantilla: str):
    """Returns the drawing function for a template, falling back to classic."""
    return DESIGN_REGISTRY.get(plantilla, draw_classic_wow)

__all__ = ['DESIGN_REGISTRY', 'get_design',
           'draw_classic_wow', 'draw_modern_wow', 'draw_geometric_wow']
