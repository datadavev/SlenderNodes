"""

"""

import datetime as dt
import io
import json
import logging
import mimetypes
import re

import dateutil.parser
import dateutil.tz
from rdflib import ConjunctiveGraph, Namespace, URIRef
from rdflib.namespace import NamespaceManager
from rdflib.tools import rdf2dot
import graphviz
import requests
from extruct.jsonld import JsonLdExtractor

# Add one mimetype to the global map.
mimetypes.init()
mimetypes.add_type('application/rdf+xml', '.rdf')

SCHEMA_ORG = "https://schema.org/"
SO_PREFIX = "SO"

SPARQL_PREFIXES = """
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX SO:   <https://schema.org/>
    PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
    PREFIX datacite: <http://purl.org/spar/datacite/>
"""

# Mapping to undo case confusion
# For example, "propertyId" should be "propertyID"
# The LHS is the lowercase match to the correct RHS value
SO_TERMS = {"propertyid": "propertyID", "dataset": "Dataset"}

# Match variants of "https://schema.org/"
RE_SO = re.compile(r"^http.{0,1}://schema\.org/{0,1}")

logger = logging.getLogger(__name__)


def _desloppifyTerm(g, t):
    """
    Deal with sloppy case consistency in SO term use

    for example:
      SO:propertyId should be SO:propertyID

    Args:
        g: graph containing t
        t: term to de-slop

    Returns:
        term, de-slopped
    """
    if isinstance(t, URIRef):
        try:
            qname = g.namespace_manager.compute_qname(t)
            # 0 = prefix, 1 = namespace, 2 = term
            if qname[0] == SO_PREFIX:
                # Check the term value for case errors
                t_val = SO_TERMS.get(qname[2].lower(), qname[2])
                if t_val != qname[2]:
                    logger.info(f"replacing SO:{qname[2]} with {t_val}")
                # return the normalized term
                return URIRef(t_val, qname[1])
        # not a qname. Odd, but continue
        except Exception:
            pass
    return t


def _normalizeTerm(t):
    """
    Hack the URIRefs to normalize schema.org to use "https://schema.org/"

    This is an ugly solution to the problem of variable representations of
    the schema.org namespace in the wild.

    Args:
        t: Graph term to process

    Returns:
        Graph term normalized to namespace <https://schema.org/>
    """
    if isinstance(t, URIRef):
        v = str(t)
        so_match = RE_SO.match(v)
        if so_match is not None:
            v = v[so_match.end():]
            if v[-1] == "/":
                v = v[:-1]
            return URIRef(v, SCHEMA_ORG)
    return t


def loadSOGraph(
    filename=None,
    data=None,
    publicID=None,
    normalize=True,
    deslop=True,
    format="json-ld",
):
    """
    Load RDF string or file to an RDFLib ConjunctiveGraph

    Creates a ConjunctiveGraph from  the provided file or text. If both are
    provided then text is used.

    NOTE: Namespace use of ``<http://schema.org>``, ``<https://schema.org>``, or
    ``<http://schema.org/>`` is normalized to ``<https://schema.org/>`` if
    ``normalize`` is True.

    NOTE: Case of ``SO:`` properties in `SO_TERMS` is adjusted consistency if
    ``deslop`` is True

    Args:
        filename (string):  path to RDF file on disk
        data (string): RDF text
        publicID (string): (from rdflib) The logical URI to use as the document base. If None specified the document location is used.
        normalize (boolean): Normalize the use of schema.org namespace
        deslop (boolean): Adjust schema.org terms for case consistency
        format (string): The serialization format of the RDF to load

    Returns:
        ConjunctiveGraph: The loaded graph

    Example:

    .. jupyter-execute:: examples/code/eg_loadsograph_01.py

    """
    g = ConjunctiveGraph()
    if data is not None:
        g.parse(data=data, format=format, publicID=publicID)
    elif filename is not None:
        g.parse(filename, format=format, publicID=publicID)
    if not (normalize or deslop):
        return g
    # Now normalize the graph namespace use to https://schema.org/
    ns = NamespaceManager(g)
    ns.bind(SO_PREFIX, SCHEMA_ORG, override=True, replace=True)
    g2 = ConjunctiveGraph()
    g2.namespace_manager = ns
    for s, p, o in g:
        trip = [s, p, o]
        if normalize:
            for i, t in enumerate(trip):
                trip[i] = _normalizeTerm(t)
        if deslop:
            for i, t in enumerate(trip):
                trip[i] = _desloppifyTerm(g, t)
        g2.add(trip)
    return g2


def loadSOGraphFromHtml(html, url):
    """
    Extract jsonld entries from provided HTML text

    Args:
        html(string): HTML text to be parsed

    Returns:
        ConjunctiveGraph: Graph loaded from html

    """
    jslde = JsonLdExtractor()
    json_content = jslde.extract(html)
    g = ConjunctiveGraph()
    for json_data in json_content:
        g_data = loadSOGraph(data=json.dumps(json_data), publicID=url)
        g += g_data
    return g


def loadSOGraphFromUrl(url):
    """
    Loads graph from json-ld contained in a landing page.

    Args:
        url (string): Url to process

    Returns:
        ConjunctiveGraph: Graph of instance

    Example:

    .. jupyter-execute:: examples/code/eg_loadfromurl_01.py
    """
    response = requests.get(url)
    if response.status_code != requests.codes.ok:
        raise ValueError(
            f"GET request to {url} returned a status of {response.status_code}"
        )
    return loadSOGraphFromHtml(response.text, response.url)


def renderGraph(g):
    """
    For rendering an rdflib graph in Jupyter notebooks

    Args:
        g (Graph): The graph to render

    Returns:
        Jupyter cell: Output for rendering directly in the notebook

    Example:

    .. jupyter-execute:: examples/code/eg_rendergraph_01.py
    """
    fp = io.StringIO()
    rdf2dot.rdf2dot(g, fp)
    return graphviz.Source(fp.getvalue())


def hasDataset(g):
    """
    Number of SO:Dataset graphs in g

    Args:
        g (Graph): The graph to evaluate

    Returns:
        integer: Number of SO:Dataset graphs in g

    Example:

    .. jupyter-execute:: examples/code/eg_hasdataset_01.py

    """
    q = (
        SPARQL_PREFIXES
        + """
    SELECT ?x 
    { 
        ?x rdf:type SO:Dataset .        
    }
    """
    )
    qres = g.query(q)
    return len(qres)


def getDateModified(g):
    """
    Retrieve literal SO:Dataset dateModified entries

    Args:
        g (Graph): Graph containing ``SO:Dataset``

    Returns:
        list: A list of ``{value:, url:, propertyId:}`` with url=None and propertyId="Literal"
    """
    q = (
        SPARQL_PREFIXES
        + """
        SELECT ?dateModified
        WHERE
        {
            ?x rdf:type SO:Dataset .
            ?x SO:encoding ?y .
            ?y SO:dateModified ?dateModified .
        }
        """
    )
    qres = g.query(q)
    items = list(qres)
    if len(items) > 0:
        date = dateutil.parser.parse(str(items[0][0]))
        date = date.replace(tzinfo=date.tzinfo or dateutil.tz.gettz("UTC"))
        return date

    # So look for it under the dataset element.
    q = (
        SPARQL_PREFIXES
        + """
        SELECT ?dateModified
        WHERE
        {
            ?x rdf:type SO:Dataset .
            ?x SO:dateModified ?dateModified .
        }
        """
    )
    qres = g.query(q)
    items = list(qres)
    if len(items) > 0:
        date = dateutil.parser.parse(str(items[0][0]))
        date = date.replace(tzinfo=date.tzinfo or dateutil.tz.gettz("UTC"))
        return date

    return None

def getLiteralDatasetIdentifiers(g):
    """
    Retrieve literal SO:Dataset.identifier entries

    Args:
        g (Graph): Graph containing ``SO:Dataset``

    Returns:
        list: A list of ``{value:, url:, propertyId:}`` with url=None and propertyId="Literal"
    """
    q = (
        SPARQL_PREFIXES
        + """
    SELECT ?y
    WHERE {
        ?x rdf:type SO:Dataset .
        ?x SO:identifier ?y .
        FILTER (isLiteral(?y)) .
    }
    """
    )
    res = []
    qres = g.query(q)
    for v in qres:
        res.append({"value": str(v[0]), "propertyId":"Literal", "url": None})
    return res


def getStructuredDatasetIdentifiers(g):
    """
    Extract structured SO:Dataset.identifier entries

    Args:
        g (Graph): Graph containing ``SO:Dataset``

    Returns:
        list: A list of ``{value:, url:, propertyId:}``
    """
    q = (
        SPARQL_PREFIXES
        + """
    SELECT DISTINCT ?value ?url ?propid
    WHERE {
        ?x rdf:type SO:Dataset .
        ?x SO:identifier ?y .
        ?y rdf:type ?tt .
        ?y SO:value ?value .
        ?y SO:propertyID ?propid .
        OPTIONAL { ?y SO:url ?url } .
        FILTER (?tt = SO:PropertyValue || ?tt = datacite:ResourceIdentifier)
    }
    """
    )
    res = []
    qres = g.query(q)
    for v in qres:
        i = {"value": str(v[0]), "url": str(v[1]), "propertyId": str(v[2])}
        res.append(i)
    return res


def getDatasetIdentifiers(g):
    """
    Return a list of ``SO:Dataset.identifier`` entries from the provided Graph

    Args:
        g (Graph): Graph containing ``SO:Dataset``

    Returns:
        list: A list of ``{value:, url:, propertyId:}``

    Example:

    .. jupyter-execute:: examples/code/eg_datasetidentifiers_01.py
    """
    # First get any identifiers that are literals with no additional context
    res = getLiteralDatasetIdentifiers(g)
    return res + getStructuredDatasetIdentifiers(g)


def getDatasetMetadataLinksFromEncoding(g):
    """
    Extract link to metadata from SO:Dataset.encoding

    Args:
        g: ConjunctiveGraph

    Returns:
        list: A list of ``{dateModified:, encodingFormat:, contentUrl:, description:, subjectOf:,}``

    Example:

    .. jupyter-execute:: examples/code/eg_metadatalinks_encoding.py
    """
    q = (
        SPARQL_PREFIXES
        + """
    SELECT ?dateModified ?encodingFormat ?contentUrl ?description ?x
    WHERE {
        ?x rdf:type SO:Dataset .
        ?x SO:encoding ?y .
        ?y SO:encodingFormat ?encodingFormat.
        ?y SO:dateModified ?dateModified .
        ?y SO:contentUrl ?contentUrl .
        ?y SO:description ?description .
    }
    """
    )
    res = []
    qres = g.query(q)
    for item in qres:
        entry = {
            "dateModified": item[0],
            "encodingFormat": str(item[1]),
            "contentUrl": str(item[2]),
            "description": str(item[3]),
            "subjectOf": str(item[4]),
        }
        res.append(entry)
    return res


def _getDatasetMetadataLinksFromSubjectOf_creative_work(g):
    q = (
        SPARQL_PREFIXES
        + """
        SELECT ?dateModified ?encodingFormat ?contentUrl ?description ?additionalDatatype ?about
        WHERE {
            ?about rdf:type SO:Dataset .
            ?about SO:subjectOf ?y .
            ?y SO:url ?contentUrl .
            ?y SO:encodingFormat ?encodingFormat .
            OPTIONAL {
              ?y SO:dateModified ?dateModified .
            } .    
            OPTIONAL {
              ?y SO:description ?description .
            } .    
            OPTIONAL {
                ?y SO:additionalType ?additionalType .
            } .
        }
        """
    )

    qres = g.query(q)
    res = _extract_DatasetMetadataLinksFromSubjectOf(qres)
    return res


def _getDatasetMetadataLinksFromSubjectOf_datadownload(g):
    q = (
        SPARQL_PREFIXES
        + """
        SELECT ?dateModified ?encodingFormat ?contentUrl ?description ?additionalType ?about
        WHERE {
            ?about rdf:type SO:Dataset .
            ?about SO:subjectOf ?y .
            ?y rdf:type SO:DataDownload .
            ?y SO:encodingFormat ?encodingFormat .
            ?y SO:contentUrl ?contentUrl .
            OPTIONAL {
                ?y SO:description ?description .
            } .
            OPTIONAL {
                ?y SO:dateModified ?dateModified .
            } .
            OPTIONAL {
                ?y SO:additionalType ?additionalType .
            } .
        }
        """
    )

    qres = g.query(q)
    res = _extract_DatasetMetadataLinksFromSubjectOf(qres)
    return res

def _extract_DatasetMetadataLinksFromSubjectOf(qres):
    """
    We have a result set from the getDatasetMetadataLinksFromSubject query.  We
    need to post process it to extract the proper information out of it.  In
    particular, the encodingFormat value that we want might be either in the
    encodingFormat field or in the additionalDatatype field.
    """
    res = []
    for item in qres:
        encodingFormat = str(item[1])

        # If the encodingFormat is a mime type, then that's a hint that the
        # value we really want was in the "additionalType"
        if encodingFormat in mimetypes.types_map.values():
            encodingFormat = str(item[4])

        entry = {
            "dateModified": item[0],
            "encodingFormat": encodingFormat,
            "contentUrl": str(item[2]),
            "description": str(item[3]),
            "subjectOf": str(item[5]),
        }
        res.append(entry)
    return res

def getDatasetMetadataLinksFromSubjectOf(g):
    """
    Extract list of metadata links from SO.Dataset.subjectOf

    Args:
        g (Graph): Graph containing the ``SO:Dataset``

    Returns:
        list: A list of ``{dateModified:, encodingFormat:, contentUrl:, description:, subjectOf:,}``

    Example:

    .. jupyter-execute:: examples/code/eg_metadatalinks_subjectof.py
    """
    # In a perfect world populated by people genetically and intellectually
    # superior to this guy, this could be done with a single SPARQL query.
    # I am not smart enough to do that.
    res = _getDatasetMetadataLinksFromSubjectOf_creative_work(g)
    if len(res) > 0:
        return res

    res = _getDatasetMetadataLinksFromSubjectOf_datadownload(g)
    return res


def getFlavorSO(g, SOFlavor):
    """
    Determine the "flavor" of the SO content.

    Args:
        g(Graph): Graph containing an ``SO:Dataset``

    Returns:
        Enumerated constant corresponding to the flavor.
    """
    # This gets info from BCO-DMO style content.
    res = _getDatasetMetadataLinksFromSubjectOf_datadownload(g)
    if len(res) > 0:
        return SOFlavor.BCO_DMO
    else:
        #  So the default will be ARM.
        return SOFlavor.ARM


def getDatasetMetadataLinksFromAbout(g):
    """
    Extract a list of metadata links SO:about(SO:Dataset)

    Args:
        g(Graph): Graph containing an ``SO:Dataset``

    Returns:
        list: A list of ``{dateModified:, encodingFormat:, contentUrl:, description:, subjectOf:,}``

    Example:

    .. jupyter-execute:: examples/code/eg_metadatalinks_about.py
    """
    q = (
        SPARQL_PREFIXES
        + """
    SELECT ?dateModified ?encodingFormat ?contentUrl ?description ?about
    WHERE {
        ?about rdf:type SO:Dataset .
        ?y SO:about ?about .
        ?y SO:contentUrl ?contentUrl .
        ?y SO:encodingFormat ?encodingFormat .
        OPTIONAL {
          ?y SO:dateModified ?dateModified .
          ?y SO:description ?description .
        }
    }
    """
    )
    res = []
    qres = g.query(q)
    for item in qres:
        entry = {
            "dateModified": item[0],
            "encodingFormat": str(item[1]),
            "contentUrl": str(item[2]),
            "description": str(item[3]),
            "subjectOf": str(item[4]),
        }
        res.append(entry)
    return res


def getDatasetMetadataLinks(g):
    """
    Extract links to metadata documents describing SO:Dataset

    Metadata docs can be referenced different ways

    * as SO:Dataset.subjectOf
    * the inverse of 1, SO:CreativeWork.about(SO:Dataset)
    * SO:Dataset.encoding

    Args:
        g (Graph): Graph containing ``SO:Dataset``

    Returns:
        list: A list of ``{dateModified:, encodingFormat:, contentUrl:, description:, subjectOf:,}``

    Example:

    .. jupyter-execute:: examples/code/eg_metadatalinks_01.py
    """
    res = getDatasetMetadataLinksFromEncoding(g)
    res += getDatasetMetadataLinksFromSubjectOf(g)
    res += getDatasetMetadataLinksFromAbout(g)
    return res
