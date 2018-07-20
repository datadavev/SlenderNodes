Slender Node Adapter Supporting schema.org described Resources
==============================================================

Notes for implementation of a "slender node" adapter to support synchronization
of content described with schema.org constructs.

Discovery Pattern
-----------------

The general pattern for discovery of schema.org resources given a domain name is:

1. parse http(s)://domain.name/robots.txt

   This step is optional if the location of the sitemap.xml is known (step 2)

2. Get the sitemap.xml file from the location identified or inferred from robots.txt

3. For each entry in the sitemap.xml file:

   a. If the entry is sitemap, go to step 2 and process the referenced sitemap.

   b. Otherwise, load and parse the resource, extract the schema.org information

   c. If sufficient and appropriate schema.org information is available, then add the
      referenced resource or resources to the set of items to be processed. Note that
      the sitemap.xml may point to Dataset or a DataCatalog instance. In the latter case,
      the DataCatalog item should be processed to discover the contained Dataset
      instances.

A schema.org Dataset instance is considered to be the target item for synchronization by
DataONE, and the Dataset should contain references to the components of the Dataset.

DataONE treats the Dataset instance as a view of the actual dataset, with parts of the
view populated from difference components of the dataset such as the metadata and
resource map or its equivalent providing relationships between components.


Dataset Constructs
------------------

This content is in DRAFT status, subject to change.

Required properties:

* identifier
* datePublished
* dateModified  (required if there are updates after datePublished)
* distribution

The distribution element must be an array of DataDownload entries, one for each component
of the dataset being desribed.

Each entry in distribution should include:

* identifier
* encodingFormat
* name
* url
* "additionalType": "http://www.w3.org/ns/dcat#DataCatalog"



