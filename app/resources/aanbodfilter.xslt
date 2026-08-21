<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.1"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:ebu="urn:ebu:metadata-schema:ebuCore_2012" exclude-result-prefixes="dc ebu">
    <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

    <!-- variables -->
    <xsl:variable name="status" select="//ebu:description[@typeDefinition='status']/dc:description"/>
    <xsl:variable name="hasBeenBroadcasted" select="//ebu:description[@typeDefinition='hasBeenBroadcasted']/dc:description"/>
    <xsl:variable name="audioOrVideo">
        <xsl:choose>
            <xsl:when test="boolean(//ebu:videoFormat/node())">video</xsl:when>
            <xsl:when test="boolean(//ebu:audioFormat/node())">audio</xsl:when>
            <xsl:otherwise></xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="productionMethod" select="//ebu:description[@typeDefinition='productionMethod']/dc:description"/>
    <xsl:variable name="ebuType" select="//ebu:type/ebu:objectType/@typeDefinition"/>
    <xsl:variable name="rightsType" select="//ebu:description[@typeDefinition='rightsType']/dc:description"/>
    <xsl:variable name="category" select="//ebu:description[@typeDefinition='category']/dc:description"/>
    <xsl:variable name="genre" select="//ebu:type/ebu:genre/@typeDefinition"/>
    <xsl:variable name="itemBehoortTotFootage" select="boolean(//ebu:relation[normalize-space(@typeDefinition) = 'FOOTAGE_HAS_ITEM'])" />

    <!-- templates -->
    <xsl:template name="aanbodfilter">
        <xsl:if test="$hasBeenBroadcasted='true'">
            <multiselect>BEZOEKERTOOL-CONTENT</multiselect>
            <multiselect>BEZOEKERTOOL-METADATA-ALL</multiselect>
            
            <xsl:if test="$status = 'gearchiveerd' and $audioOrVideo != ''">
                <xsl:choose>
                    <xsl:when test="($productionMethod != 'aankoop') and (($ebuType = 'item') or ($ebuType = 'online_item') or ($ebuType = 'program')) and ($rightsType = '' or $rightsType = 'vrij gebruik') and ($itemBehoortTotFootage = 'false')">
                        <xsl:choose>
                            <xsl:when test="($audioOrVideo = 'video' and ($category != 'sport' and $genre != 'fictie') or ($audioOrVideo = 'audio' and $category = 'nieuws en duiding'))">
                                <multiselect>VIAA-ONDERWIJS</multiselect>
                                <multiselect>VIAA-ONDERZOEK</multiselect>
                                <multiselect>VIAA-INTRA_CP-CONTENT</multiselect>
                                <multiselect>VIAA-INTRA_CP-METADATA-ALL</multiselect>
                                <multiselect>VIAA-PUBLIEK-METADATA-LTD</multiselect>
                            </xsl:when>
                            <xsl:when test="($audioOrVideo = 'video' and (($category = 'sport' and $genre != 'fictie') or ($category != 'sport' and $genre = 'fictie')) or ($audioOrVideo = 'audio' and $category != 'nieuws en duiding'))">
                                <multiselect>VIAA-INTRA_CP-METADATA-ALL</multiselect>
                                <multiselect>VIAA-PUBLIEK-METADATA-LTD</multiselect>
                            </xsl:when>
                            <xsl:otherwise></xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                </xsl:choose>
            </xsl:if>
        </xsl:if>
    </xsl:template>
</xsl:stylesheet>
