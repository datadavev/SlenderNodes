<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:template match="/">
	  <html>
	  <head>
	  <style>
	    table {
	      border-collapse: collapse;
	    }
	    td, th {
	      padding: 2px 5px 2px 5px;
	    }
      .nowrap {
        white-space: nowrap;
      }
	  </style>
	  </head>
	  <body>
	  <h2>PASTA GMN Adapter | <a href="../admin">Admin</a> | Population Queue</h2>
	  <table border="1">
	    <tr bgcolor="lightblue">
	      <th colspan="5">Package</th>
	      <th colspan="5">Last Process Status</th>
	    </tr>
	    <tr bgcolor="lightblue">
	      <th>ID</th>
	      <th>Scope</th>
	      <th>Identifier</th>
	      <th>Revision</th>
	      <th>Queued</th>

	      <th>Processed</th>
	      <th>Status</th>
	      <th>Code</th>
	      <th>Message (256 first chars)</th>
        <th>Log</th>
	    </tr>
	    <xsl:for-each select="population_queue/package">
	    <tr>
        <td><xsl:value-of select="id"/></td>
        <td class="nowrap"><xsl:value-of select="scope"/></td>
	      <td class="nowrap"><xsl:value-of select="identifier"/></td>
	      <td class="nowrap"><xsl:value-of select="revision"/></td>
	      <td class="nowrap"><xsl:value-of select="timestamp_queued"/></td>

	      <td class="nowrap"><xsl:value-of select="timestamp_processed"/></td>
        <td class="nowrap"><xsl:value-of select="status" /></td>
        <td class="nowrap"><xsl:value-of select="return_code" /></td>
        <td><xsl:value-of select="return_body" /></td>

	      <td>
	        <xsl:element name="a">
	          <xsl:attribute name="href">
	            <xsl:text>status/</xsl:text>
              <xsl:value-of select="id" />
            </xsl:attribute>
            Log
          </xsl:element>
	      </td>

	    </tr>
	    </xsl:for-each>
	  </table>
	  </body>
	  </html>
	</xsl:template>
</xsl:stylesheet>
