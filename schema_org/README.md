# Slender Node Adapter Supporting schema.org described Resources

Notes for implementation of a "slender node" adapter to support synchronization
of content described with `schema.org` (SO) constructs.

## Discovery Pattern

The general pattern for discovery of SO resources given a domain name is:

1. parse `http(s)://domain.name/robots.txt`

   This step is optional if the location of the `sitemap.xml` is known (step 2)

2. Get the `sitemap.xml` file from the location identified or inferred from `robots.txt`

3. For each entry in the `sitemap.xml` file:

   a. If the entry is sitemap, go to step 2 and process the referenced sitemap.

   b. Otherwise, load and parse the resource, extract the SO information

   c. If sufficient and appropriate SO information is available, then add the
      referenced resource or resources to the set of items to be processed.

A `schema:Dataset` instance is the target for synchronization by DataONE. The
`Dataset` must contain certain expected properties in order to be recognized
by DataONE for synchronization.

## DataONE requirements for `schema:Dataset`

Given:

```
PREFIX schema = <https://schema.org/>
```

For `schema:Dataset` described on the landing page at `https://example.org/sample/landing/page.html`,
the dataset has a DOI `10.1234/abcd` and an ISO TC 211 copy of the metadata
available at the location `https://example.org/link/to/iso.xml`. The dataset
has a single component of data in `text/csv` format that is located at
`https://example.org/link/to/data.csv` and has an identifier of
`uuid:ef74c986-bf6e-11e9-9cb5-2a2ae2dbcce4`.

```
{
    "@context":{
        "@vocab": "http://schema.org/",
        "datacite": "http://purl.org/spar/datacite/"
    },
    "@id":"https://example.org/sample/landing/page.html",
    "@type": "Dataset",

    "identifier": {
        "@type": ["PropertyValue", "datacite:ResourceIdentifier"],
        "datacite:usesIdentifierScheme": {
            "@id": "datacite:doi"
        },
        "propertyId":"DOI",
        "url": "https://doi.org/10.1234/abcd",
        "value": "10.1234/abcd"
    },
    "encoding":{
        "@type": "MediaObject",
        "contentUrl":"https://example.org/link/to/iso.xml",
        "encodingFormat":"http://www.isotc211.org/2005/gmd",
        "description":"ISO TC211 XML rendering of metadata.",
        "dateModified":"2019-06-12T14:44:15Z"
    },
    "distribution": [
        {
            "@type":"DataDownload",
            "contentUrl":"https://example.org/link/to/data.csv",
            "identifier": {
                "@type": ["PropertyValue", "datacite:ResourceIdentifier"],
                "datacite:usesIdentifierScheme": {
                    "@id": "datacite:local-resource-identifier-scheme"
                },
                "propertyId":"UUID",
                "value": "uuid:ef74c986-bf6e-11e9-9cb5-2a2ae2dbcce4"              
            },
            "encodingFormat":"text/csv",
            "description":"Comma separated data",
            "dateModified":"2019-06-12T14:44:15Z"            
            }
        }
    ]
}
```
