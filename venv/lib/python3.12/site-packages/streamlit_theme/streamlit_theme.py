try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources
from string import Template 

from .helpers import hex_to_rgb
from . import templates

import streamlit as st


def set_theme(options):
    s = Template(pkg_resources.read_text(templates, 'main.css'))
    css = s.substitute(primaryHex=options['primary'],
                       primaryRGB=hex_to_rgb(options['primary']))
    return st.markdown('<style>' + css.replace('\n','') + '</style>', unsafe_allow_html=True)

