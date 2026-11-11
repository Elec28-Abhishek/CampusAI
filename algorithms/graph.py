"""VSSUT road graph adapter. Unverified demonstration edges are labeled in data."""

from data.campus import graph_from_data, load_campus_data


GRAPH = graph_from_data(load_campus_data())
