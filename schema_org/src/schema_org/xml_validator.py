# Standard library imports ...
import io
import pathlib

# Third party library imports ...
import lxml.etree
import requests

# Before this schema can be used, the install root must be interpolated.
_SCHEMA_DOC = """
<!--
    Nov 20, 2009, AMilan
    changed targetNamespace to gmi and changed include to gmi.xsd

    Apr 29, 2016, JEvans
    Add install_root, to be interpolated to schema installation directory.
-->
<xs:schema
    targetNamespace="http://www.isotc211.org/2005/gmi"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:gmi="http://www.isotc211.org/2005/gmi"
    xmlns:srv="http://www.isotc211.org/2005/srv">

    <xs:include
        schemaLocation="{install_root}/schema/gmi/gmi.xsd"/>
    <xs:import
        namespace="http://www.isotc211.org/2005/gmd"
        schemaLocation="{install_root}/schema/gmd/gmd.xsd"/>
    <xs:import
        namespace="http://www.isotc211.org/2005/srv"
        schemaLocation="{install_root}/schema/srv/srv.xsd"/>

</xs:schema>
"""


class XMLValidator(object):
    """
    Validates XML files according to 19115-2 schema.
    """
    def __init__(self):
        """
        Load the 19115-2 schema so that every XML file produced is validated.
        """
        # Interpolate the path to the XSD files.
        path = pathlib.Path(__file__).parent / 'data'
        schema_doc = _SCHEMA_DOC.format(install_root=path.as_uri())
        f = io.StringIO(schema_doc)
        self.schema = lxml.etree.XMLSchema(file=f)

    def validate(self, src):
        """
        Validate the XML of the given schema.

        Parameters
        ----------
        src : str or file-like
           file or URL to validate
        """
        # Is it file or file-like, but not a path.
        try:
            doc = lxml.etree.parse(src)
        except Exception:
            # OSError:  if a string that doesn't exist on filesystem
            # TypeError:  if the item is already an ElementTree
            pass
        else:
            # The src was file or file-like object.
            self.schema.assertValid(doc)
            return

        # Is it a URL?
        try:
            r = requests.get(src)
            r.raise_for_status()
        except Exception:
            # Not a valid URL
            pass
        else:
            doc = lxml.etree.parse(io.BytesIO(r.content))
            self.schema.assertValid(doc)
            return

        # Is it a pathlib object?
        try:
            doc = lxml.etree.parse(str(src))
        except Exception:
            # OSError:  if a string that doesn't exist on filesystem
            # TypeError:  if the item is already an ElementTree
            pass
        else:
            # The src was file or file-like object.
            self.schema.assertValid(doc)
            return

        # Assume it is already an ElementTree
        self.schema.assertValid(src)
