# -*- coding: utf-8 -*-
"""
Tests for vector_tile/encoder.py
"""
import sys
import unittest

import mapbox_vector_tile
from mapbox_vector_tile import encode, decode

from shapely import wkt

PY3 = sys.version_info[0] == 3


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.layer_name = "water"
        self.feature_properties = {
            "uid": 123,
            "foo": "bar",
            "baz": "foo"
        }
        self.feature_geometry = 'POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))'

    def assertRoundTrip(self, input_geometry, expected_geometry, name=None,
                        properties=None, id=None, expected_len=1):
        if input_geometry is None:
            input_geometry = self.feature_geometry
        if name is None:
            name = self.layer_name
        if properties is None:
            properties = self.feature_properties
        source = [{
            "name": name,
            "features": [{
                "geometry": input_geometry,
                "properties": properties
            }]
        }]
        if id:
            source[0]['features'][0]['id'] = id
        encoded = encode(source)
        decoded = decode(encoded)
        self.assertIn(name, decoded)
        features = decoded[name]
        self.assertEqual(expected_len, len(features))
        self.assertEqual(features[0]['properties'], properties)
        self.assertEqual(features[0]['geometry'], expected_geometry)
        if id:
            self.assertEqual(decoded[name][0]['id'], id)


class TestDifferentGeomFormats(BaseTestCase):

    def test_encoder(self):
        self.assertRoundTrip(
            input_geometry='POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))',
            expected_geometry=[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]])

    def test_with_wkt(self):
        self.assertRoundTrip(
            input_geometry="LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)",  # noqa
            expected_geometry=[[-71, 43], [-71, 43], [-71, 43]])

    def test_with_wkb(self):
        self.assertRoundTrip(
            input_geometry=b"\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000",  # noqa
            expected_geometry=[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]])

    def test_with_shapely(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"  # noqa
        geometry = wkt.loads(geometry)
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[-71, 43], [-71, 43], [-71, 43]])

    def test_with_invalid_geometry(self):
        expected_result = ('Can\'t do geometries that are not wkt, wkb, or '
                           'shapely geometries')
        with self.assertRaises(NotImplementedError) as ex:
            mapbox_vector_tile.encode([{
                "name": self.layer_name,
                "features": [{
                    "geometry": "xyz",
                    "properties": self.feature_properties
                }]
            }])
        self.assertEqual(str(ex.exception), expected_result)

    def test_encode_unicode_property(self):
        if PY3:
            func = str
        else:
            func = unicode
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"  # noqa
        properties = {
            "foo": func(self.feature_properties["foo"]),
            "baz": func(self.feature_properties["baz"]),
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[-71, 43], [-71, 43], [-71, 43]],
            properties=properties)

    def test_encode_unicode_property_key(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"  # noqa
        properties = {
            u'☺': u'☺'
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[-71, 43], [-71, 43], [-71, 43]],
            properties=properties)

    def test_encode_float_little_endian(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"  # noqa
        properties = {
            'floatval': 3.14159
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[-71, 43], [-71, 43], [-71, 43]],
            properties=properties)

    def test_encode_feature_with_id(self):
        geometry = 'POINT(1 1)'
        self.assertRoundTrip(input_geometry=geometry,
                             expected_geometry=[[1, 1]], id=42)

    def test_encode_multipolygon(self):
        geometry = 'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))'  # noqa
        self.assertRoundTrip(input_geometry=geometry,
                             expected_geometry=[[40, 40], [20, 45], [45, 30], [40, 40]],  # noqa
                             expected_len=2)
