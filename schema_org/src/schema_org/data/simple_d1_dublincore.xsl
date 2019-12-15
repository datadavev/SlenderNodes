<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" 
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcterms="http://purl.org/dc/terms/"
    xmlns:hsterms="http://hydroshare.org/terms/"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template match="/rdf:RDF">

	<metadata
	    xmlns="http://ns.dataone.org/metadata/schema/onedcx/v1.0"
	    xmlns:dcterms="http://purl.org/dc/terms/"
	    xmlns:xhtml="http://www.w3.org/1999/xhtml"
	    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	    xsi:schemaLocation="http://ns.dataone.org/metadata/schema/onedcx/v1.0 http://ns.dataone.org/metadata/schema/onedcx/v1.0/onedcx_v1.0.xsd">
	    <simpleDc>
		<dcterms:type>Dataset</dcterms:type>
		<xsl:apply-templates select="rdf:Description/dc:title"/>
		<xsl:apply-templates select="rdf:Description/dc:creator/rdf:Description/hsterms:name"/>
		<xsl:apply-templates select="rdf:Description/dc:subject"/>
		<xsl:apply-templates select="rdf:Description/dc:description/rdf:Description/dcterms:abstract"/>
		<xsl:apply-templates select="rdf:Description/dc:publisher/rdf:Description/hsterms:publisherName"/>
		<xsl:apply-templates select="rdf:Description/dc:contributor/rdf:Description/hsterms:name"/>
		<xsl:apply-templates select="rdf:Description/dc:date/dcterms:created/rdf:value"/>
		    <!-- type? -->
		<xsl:apply-templates select="rdf:Description/dc:format"/>
		<xsl:apply-templates select="rdf:Description/dc:identifier/rdf:Description/hsterms:doi"/>
		<xsl:apply-templates select="rdf:Description/dc:identifier/rdf:Description/hsterms:hydroShareIdentifier"/>
		<xsl:apply-templates select="rdf:Description/dc:source"/>
		<xsl:apply-templates select="rdf:Description/dc:language"/>
		<!--
		<xsl:apply-templates select="rdf:Description/dc:relation"/>
		-->
		    <!-- coverage? -->
		<xsl:apply-templates select="rdf:Description/dc:rights"/>
	    </simpleDc>
	    <dcTerms>
		    <!-- alternative? -->
		    <!-- tableOfContents? -->
		    <!-- abstract a duplicate of description? -->
		<xsl:apply-templates select="rdf:Description/dc:date/dcterms:created"/>
		    <!-- valid? -->
		    <!-- difference between available and dateAccepted? -->
		<xsl:apply-templates select="rdf:Description/dc:date/dcterms:published"/>
		<xsl:apply-templates select="rdf:Description/dc:date/dcterms:issued"/>
		<xsl:apply-templates select="rdf:Description/dc:date/dcterms:modified"/>
		<xsl:apply-templates select="rdf:Description/dc:date/dcterms:dateCopyrighted"/>
		<xsl:apply-templates select="rdf:Description/dc:date/dcterms:dateSubmitted"/>
		    <!-- extent? -->
		    <!-- medium? -->
		<xsl:apply-templates select="rdf:Description/dc:relation/rdf:Description/dcterms:isVersionOf"/>
		    <!-- hasVersion? -->
		<xsl:apply-templates select="rdf:Description/dc:relation/rdf:Description/dcterms:isReplacedBy"/>
		    <!-- replaces? -->
		    <!-- isRequiredBy? -->
		    <!-- requires? -->
		<xsl:apply-templates select="rdf:Description/dc:relation/rdf:Description/dcterms:isPartOf"/>
		<xsl:apply-templates select="rdf:Description/dc:relation/rdf:Description/dcterms:hasPart"/>
		    <!-- isReferencedBy? -->
		    <!-- references? -->
		    <!-- isFormatOf? -->
		    <!-- hasFormat? -->
		    <!-- conformsTo? -->
		<xsl:apply-templates select="rdf:Description/hsterms:spatialReference"/>
		<xsl:apply-templates select="rdf:Description/dc:coverage/dcterms:period"/>
		    <!-- audience? -->
		    <!-- accruelMethod -->
		    <!-- accruelPeriodicity -->
		    <!-- accruelPolicy -->
		    <!-- instructionalMethod -->
		    <!-- provenance -->
		    <!-- rightsHolder -->
		    <!-- accessRights -->
		    <!-- license:  duplicate of rights? -->
		    <!-- bibliographicCitation -->
	    </dcTerms>
	</metadata>

    </xsl:template>

    <xsl:template match="rdf:Description/dc:title">
        <dcterms:title><xsl:value-of select="."/></dcterms:title>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:creator/rdf:Description/hsterms:name">
        <dcterms:creator><xsl:value-of select="."/></dcterms:creator>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:subject">
        <dcterms:subject><xsl:value-of select="."/></dcterms:subject>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:description/rdf:Description/dcterms:abstract">
        <dcterms:description><xsl:value-of select="."/></dcterms:description>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:publisher/rdf:Description/hsterms:publisherName">
        <dcterms:publisher><xsl:value-of select="."/></dcterms:publisher>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:contributor/rdf:Description/hsterms:name">
        <dcterms:contributor><xsl:value-of select="."/></dcterms:contributor>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:date/dcterms:created/rdf:value">
        <dcterms:date><xsl:value-of select="."/></dcterms:date>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:format">
        <dcterms:format><xsl:value-of select="."/></dcterms:format>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:identifier/rdf:Description/hsterms:doi">
        <dcterms:identifier><xsl:value-of select="."/></dcterms:identifier>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:identifier/rdf:Description/hsterms:hydroShareIdentifier">
        <dcterms:identifier><xsl:value-of select="."/></dcterms:identifier>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:source">
	<dcterms:source><xsl:value-of select="rdf:Description/hsterms:isDerivedFrom"/></dcterms:source>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:language">
	<dcterms:language><xsl:value-of select="."/></dcterms:language>
    </xsl:template>

    <xsl:template match="rdf:Description/hsterms:cites">
	<dcterms:relation><xsl:value-of select="."/></dcterms:relation>
    </xsl:template>

    <xsl:template match="rdf:Description/hsterms:spatialReference">
	<dcterms:spatial><xsl:value-of select="hsterms:box/rdf:value"/></dcterms:spatial>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:rights">
	<dcterms:rights><xsl:value-of select="rdf:Description/hsterms:rightsStatement"/></dcterms:rights>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:date/dcterms:created">
	<dcterms:created><xsl:value-of select="rdf:value"/></dcterms:created>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:date/dcterms:published">
	<dcterms:available><xsl:value-of select="rdf:value"/></dcterms:available>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:date/dcterms:issued">
	<dcterms:issued><xsl:value-of select="rdf:value"/></dcterms:issued>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:date/dcterms:modified">
	<dcterms:modified><xsl:value-of select="rdf:value"/></dcterms:modified>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:date/dcterms:dateCopyrighted">
	<dcterms:dateCopyrighted><xsl:value-of select="rdf:value"/></dcterms:dateCopyrighted>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:date/dcterms:dateSubmitted">
	<dcterms:dateSubmitted><xsl:value-of select="rdf:value"/></dcterms:dateSubmitted>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:relation/rdf:Description/dcterms:isVersionOf">
	<dcterms:isVersionOf><xsl:value-of select="@rdf:resource"/></dcterms:isVersionOf>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:relation/rdf:Description/dcterms:isReplacedBy">
	<dcterms:isReplacedBy><xsl:value-of select="@rdf:resource"/></dcterms:isReplacedBy>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:relation/rdf:Description/dcterms:isPartOf">
	<dcterms:isPartOf><xsl:value-of select="."/></dcterms:isPartOf>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:relation/rdf:Description/dcterms:hasPart">
	<dcterms:hasPart><xsl:value-of select="@rdf:resource"/></dcterms:hasPart>
    </xsl:template>

    <xsl:template match="rdf:Description/dc:coverage/dcterms:period">
	<dcterms:temporal><xsl:value-of select="rdf:value"/></dcterms:temporal>
    </xsl:template>

</xsl:stylesheet>

