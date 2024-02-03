<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:ebu="urn:ebu:metadata-schema:ebuCore_2012"
    xmlns:mh="https://zeticon.mediahaven.com/metadata/19.2/mh/"
    xmlns:vrt="http://this.this.com"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:ns8="http://www.vrt.be/mig/viaa"
    exclude-result-prefixes="dc xs ebu ns8">

    <xsl:output method="xml" encoding="UTF-8" byte-order-mark="no" indent="yes"/>

    <!-- variables -->
    <xsl:variable name="framerate">
        <xsl:choose>
            <xsl:when test="(//ebu:format[@formatDefinition='current'])[1]/ebu:videoFormat/ebu:frameRate">
                <xsl:value-of select="(//ebu:format[@formatDefinition='current'])[1]/ebu:videoFormat/ebu:frameRate"/>
            </xsl:when>
            <xsl:otherwise>25</xsl:otherwise>
        </xsl:choose>
    </xsl:variable>

    <!-- Use the named template for timecode to frames conversion -->
    <xsl:variable name="StartOfMedia">
        <xsl:call-template name="vrt:timecodeToFrames">
            <xsl:with-param name="time" select="(//ebu:format[@formatDefinition='current'])[1]/ebu:technicalAttributeString[@typeDefinition='SOM']"/>
            <xsl:with-param name="StartOfMedia" select="''"/>
        </xsl:call-template>
    </xsl:variable>


    <xsl:variable name="StartOfContent">
        <xsl:choose>
            <xsl:when test="(//ebu:format[@formatDefinition='current'])[1]/ebu:start/ebu:timecode">
                <xsl:call-template name="vrt:timecodeToFrames">
                    <xsl:with-param name="time" select="(//ebu:format[@formatDefinition='current'])[1]/ebu:start/ebu:timecode"/>
                    <xsl:with-param name="StartOfMedia" select="$StartOfMedia"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>0</xsl:otherwise>
        </xsl:choose>
    </xsl:variable>

    <xsl:variable name="EndOfContent">
        <xsl:choose>
            <xsl:when test="(//ebu:format[@formatDefinition='current'])[1]/ebu:end/ebu:timecode">
                <xsl:call-template name="vrt:timecodeToFrames">
                    <xsl:with-param name="time" select="(//ebu:format[@formatDefinition='current'])[1]/ebu:end/ebu:timecode"/>
                    <xsl:with-param name="StartOfMedia" select="$StartOfMedia"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="vrt:timecodeToFrames">
                    <xsl:with-param name="time" select="//ebu:description[@typeDefinition='duration']/dc:description"/>
                    <xsl:with-param name="StartOfMedia" select="$StartOfMedia"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>

    <!-- Named template for timecode to frames conversion -->
    <xsl:template name="vrt:timecodeToFrames">
        <xsl:param name="time"/>
        <xsl:param name="StartOfMedia"/>
        
        <xsl:variable name="hours" select="number(substring($time, 1, 2))"/>
        <xsl:variable name="minutes" select="number(substring($time, 4, 2))"/>
        <xsl:variable name="seconds" select="number(substring($time, 7, 2))"/>
        <xsl:variable name="frames" select="number(substring($time, 10, 2))"/>
        
        <xsl:variable name="timeInSeconds" select="($hours * 3600 + $minutes * 60 + $seconds)"/>
        
        <!-- Convert timecode to frames -->
        <xsl:value-of select="$timeInSeconds * 25 + floor($frames * (25 div $framerate))"/>
    </xsl:template>


    <xsl:template name="structural">
        <mh:FragmentStartFrames>
            <xsl:value-of select="$StartOfContent"/>
        </mh:FragmentStartFrames>
        <mh:FragmentEndFrames>
            <xsl:value-of select="$EndOfContent"/>
        </mh:FragmentEndFrames>
    </xsl:template>
</xsl:stylesheet>
