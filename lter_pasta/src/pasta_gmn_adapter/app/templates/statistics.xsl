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
    </style>
    </head>
    <body>
    <h2>PASTA GMN Adapter | <a href="../admin">Admin</a> | Statistics</h2>
    <table border="1">
      <tr bgcolor="lightblue">
        <th>Text</th>
        <th>Value</th>
      </tr>
      <xsl:for-each select="statistics/item">
      <tr>
        <td><xsl:value-of select="text"/></td>
        <td><xsl:value-of select="value"/></td>
      </tr>
      </xsl:for-each>
    </table>
    </body>
    </html>
  </xsl:template>
</xsl:stylesheet> 
