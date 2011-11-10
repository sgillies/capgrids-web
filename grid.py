from itertools import product
from string import Template

from capgrids import data, box, grid
import geojson
from rdflib import Literal, Namespace, RDF, URIRef
from rdflib.graph import Graph
from shapely import geometry
from shapely import wkt

FOAF_URI = "http://xmlns.com/foaf/0.1/"
FOAF = Namespace(FOAF_URI)

GEO_URI = "http://www.w3.org/2003/01/geo/wgs84_pos#"
GEO = Namespace(GEO_URI)

OSGEO_URI = "http://data.ordnancesurvey.co.uk/ontology/geometry/"
OSGEO = Namespace(OSGEO_URI)

SKOS_URI = "http://www.w3.org/2004/02/skos/core#"
SKOS = Namespace(SKOS_URI)

RDFS_URI = "http://www.w3.org/2000/01/rdf-schema#"
RDFS = Namespace(RDFS_URI)

SPATIAL_URI = "http://geovocab.org/spatial#"
SPATIAL = Namespace(SPATIAL_URI)

OSSPATIAL_URI = "http://data.ordnancesurvey.co.uk/ontology/spatialrelations/"
OSSPATIAL = Namespace(OSSPATIAL_URI)

PLACES = "http://pleiades.stoa.org/places/"

def group(number):
    s = '%d' % number
    groups = []
    while s and s[-1].isdigit():
        groups.append(s[-3:])
        s = s[:-3]
    groups.reverse()
    return s + ','.join(groups)


template = Template(open("template.html", "r").read())

for mapnum, records in data.items():
    record = records[0]
    title = record[1]
    scale = "1:%s" % group(int(record[2])*1000)
    cols = "%s-%s" % (record[7].upper(), record[8].upper())
    rows = "%s-%s" % (record[9], record[10])
    bounds = box(mapnum)
    
    # HTML
    html = template.substitute(
        mapnum=mapnum, 
        title=title, 
        scale=scale, 
        cols=cols, 
        rows=rows, 
        bounds=str(bounds)
        )
    with open("htdocs/%s.html" % mapnum, "w") as f:
        f.write(html)

    # RDF
    g = Graph()
    g.bind('rdfs', RDFS)
    g.bind('skos', SKOS)
    g.bind('spatial', SPATIAL)
    g.bind('geo', GEO)
    g.bind('foaf', FOAF)
    g.bind('osgeo', OSGEO)
    g.bind('osspatial', OSSPATIAL)

    map_uri = "http://atlantides.org/capgrids/%s" % mapnum
    map_ref = URIRef(map_uri + "#this")

    g.add((map_ref, FOAF['primaryTopicOf'], URIRef(map_uri + ".html")))
    g.add((map_ref, RDFS['label'], Literal(title)))
    map_extent = URIRef(map_uri + "#this-extent")
    g.add((map_extent, RDF.type, OSGEO['AbstractGeometry']))
    g.add((map_ref, OSGEO['extent'], map_extent))
    g.add((
        map_extent, 
        OSGEO['asGeoJSON'], 
        Literal(geojson.dumps(geometry.box(*bounds)))))
    g.add((
        map_extent, 
        OSGEO['asWKT'], 
        Literal(wkt.dumps(geometry.box(*bounds)))))

    # Individual Grid cells
    cols, rows = grid(mapnum)
    for col, row in product(cols, rows):
        key = col.upper() + str(row)
        bounds = box(mapnum, key)

        grid_uri = map_uri + "#" + key
        grid_ref = URIRef(grid_uri)
        grid_extent_ref = URIRef(grid_uri + "-extent")

        g.add((grid_ref, RDFS['label'], Literal("Grid Cell " + key)))
        g.add((grid_extent_ref, RDF.type, OSGEO['AbstractGeometry']))
        g.add((grid_ref, OSGEO['extent'], grid_extent_ref))
        g.add((
            grid_extent_ref, 
            OSGEO['asGeoJSON'], 
            Literal(geojson.dumps(geometry.box(*bounds)))))
        g.add((
            grid_extent_ref, 
            OSGEO['asWKT'], 
            Literal(wkt.dumps(geometry.box(*bounds)))))
        
        g.add((map_ref, OSSPATIAL['contains'], grid_ref))


    with open("htdocs/%s.ttl" % mapnum, "w") as f:
        f.write(g.serialize(format="turtle"))


