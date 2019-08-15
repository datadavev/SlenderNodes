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
    <h2>PASTA GMN Adapter | <a href="../../admin">Admin</a> | <a href="../population_queue">Population Queue</a> | Status</h2>
    <table border="1">
      <tr bgcolor="lightblue">
        <th>ID</th>
        <th>Processed</th>
        <th>Return Code</th>
        <th>Return Body</th>
      </tr>
      <xsl:for-each select="status_log/status">
      <tr>
        <td><xsl:value-of select="id"/></td>
        <td><xsl:value-of select="timestamp"/></td>
        <td><xsl:value-of select="return_code"/></td>
        <td><xsl:value-of select="return_body"/></td>
      </tr>
      </xsl:for-each>
    </table>
    </body>
    </html>
  </xsl:template>
</xsl:stylesheet> 
