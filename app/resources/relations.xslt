<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.1"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:ebu="urn:ebu:metadata-schema:ebuCore_2012"
    exclude-result-prefixes="dc ebu">

    <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

    <!-- Relations mapping -->
    <xsl:template name="relations">
        <xsl:for-each select="//ebu:relation[ebu:relationIdentifier/dc:identifier]">
            <xsl:variable name="relationType" select="normalize-space(@typeDefinition)"/>
            <xsl:variable name="mappedRelation">
                <xsl:choose>
                    <xsl:when test="$relationType = 'Programma verwijst naar item'">PROGRAM_REFERENCES_ITEM</xsl:when>
                    <xsl:when test="$relationType = 'Item verwijst naar Programma'">PROGRAM_REFERENCES_ITEM</xsl:when>
                    <xsl:when test="$relationType = 'Programma gebruikt footage'">PROGRAM_USES_FOOTAGE</xsl:when>
                    <xsl:when test="$relationType = 'Footage wordt gebruikt in programma'">PROGRAM_USES_FOOTAGE</xsl:when>
                    <xsl:when test="$relationType = 'Programma verwijst naar programma'">PROGRAM_HAS_PROGRAM</xsl:when>
                    <xsl:when test="$relationType = 'Programma verwijst naar trailer'">PROGRAM_HAS_TRAILER</xsl:when>
                    <xsl:when test="$relationType = 'Trailer verwijst naar programma'">PROGRAM_HAS_TRAILER</xsl:when>
                    <xsl:when test="$relationType = 'Trailer verwijst naar trailer'">TRAILER_HAS_TRAILER</xsl:when>
                    <xsl:when test="$relationType = 'Footage verwijst naar footage'">FOOTAGE_HAS_FOOTAGE</xsl:when>
                    <xsl:when test="$relationType = 'Trailer gebruikt footage'">TRAILER_USES_FOOTAGE</xsl:when>
                    <xsl:when test="$relationType = 'Footage wordt gebruikt in trailer'">TRAILER_USES_FOOTAGE</xsl:when>
                    <xsl:when test="$relationType = 'Item gebruikt footage'">ITEM_USES_FOOTAGE</xsl:when>
                    <xsl:when test="$relationType = 'Footage wordt gebruikt in item'">ITEM_USES_FOOTAGE</xsl:when>
                    <xsl:when test="$relationType = 'Item verwijst naar item'">ITEM_HAS_ITEM</xsl:when>
                    <xsl:when test="$relationType = 'Seizoen heeft programma'">SEASON_HAS_PROGRAM</xsl:when>
                    <xsl:when test="$relationType = 'Programma behoort tot seizoen'">SEASON_HAS_PROGRAM</xsl:when>
                    <xsl:when test="$relationType = 'Footage heeft item'">FOOTAGE_HAS_ITEM</xsl:when>
                    <xsl:when test="$relationType = 'Item behoort tot footage'">FOOTAGE_HAS_ITEM</xsl:when>
                    <xsl:when test="$relationType = 'Programma heeft item'">PROGRAM_HAS_ITEM</xsl:when>
                    <xsl:when test="$relationType = 'Item behoort tot programma'">PROGRAM_HAS_ITEM</xsl:when>
                    <!-- Add other mappings as needed -->
                    <xsl:otherwise></xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            
            <xsl:if test="$mappedRelation != ''">
                <xsl:element name="{$mappedRelation}">
                    <xsl:value-of select="ebu:relationIdentifier/dc:identifier"/>
                </xsl:element>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
</xsl:stylesheet>
