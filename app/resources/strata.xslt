<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.1"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:ebu="urn:ebu:metadata-schema:ebuCore_2012">

    <xsl:output method="xml" encoding="UTF-8"/>

    <xsl:template name="strata">
        <xsl:for-each select="//ebu:part">
            <!-- &#10; is a newline -->
            <xsl:text>&#10;</xsl:text>
            <xsl:value-of select="ebu:partStartTime/ebu:timecode"/>
            <xsl:text> </xsl:text>
            <xsl:value-of select="ebu:description/dc:description"/>
        </xsl:for-each>
    </xsl:template>
</xsl:stylesheet>