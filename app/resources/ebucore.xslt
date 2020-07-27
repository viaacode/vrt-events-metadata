<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:dc="http://purl.org/dc/elements/1.1/" 
    xmlns:ebu="urn:ebu:metadata-schema:ebuCore_2012" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:viaa="http://www.vrt.be/mig/viaa/api"
    xsi:schemaLocation="urn:ebu:metadata-schema:ebucore https://www.ebu.ch/metadata/schemas/EBUCore/20171009/ebucore.xsd"
    version="3.0"
    exclude-result-prefixes="xsl viaa">
    <xsl:output method="xml" encoding="UTF-8" byte-order-mark="no" indent="yes"/>
    <xsl:template match="/">
        <ebu:ebuCoreMain>
            <ebu:coreMetadata>
                <xsl:copy-of select="*/viaa:metadata/*" copy-namespaces="no"/>
            </ebu:coreMetadata>
        </ebu:ebuCoreMain>
    </xsl:template>
</xsl:stylesheet>