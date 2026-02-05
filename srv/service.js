const cds = require('@sap/cds');

/**
 * Implementation of MassChangeService
 * Converts Joule JSON requests to S/4HANA batch OData multipart
 */
module.exports = cds.service.impl(async function () {

  // Connect to S/4HANA destination configured in package.json
  const s4Service = await cds.connect.to('SB4_ODATA');
  
  if (!s4Service) {
    throw new Error('Unable to connect to S4HANA_PCE_SSO destination. Check BTP destination configuration.');
  }
  
  console.log('[Mass Change] Successfully connected to S4HANA destination');

  /**
   * Handler for scheduleMassChange action
   * Receives filters and fields from Joule, builds batch payload, sends to S/4HANA
   */
  this.on('scheduleMassChange', async (req) => {
    const { filters, fieldsToUpdate } = req.data;
    
    console.log('[Mass Change] Request received from Joule:', JSON.stringify(req.data, null, 2));

    // Validate required fields
    if (!filters || !fieldsToUpdate) {
      return {
        ID: cds.utils.uuid(),
        status: 'ERROR',
        jobName: 'Mass Field Update from Joule',
        timestamp: new Date().toISOString(),
        message: 'Missing required parameters: filters or fieldsToUpdate',
        fioriAppLink: ''
      };
    }

    try {
      // 1. Fetch CSRF token from S/4HANA (required for POST operations)
      console.log('[Mass Change] Fetching CSRF token from S/4HANA...');
      const csrfResponse = await s4Service.send({
        method: 'GET',
        path: '/',
        headers: {
          'X-CSRF-Token': 'Fetch',
          'Accept': 'application/json'
        }
      });
      
      const csrfToken = csrfResponse.headers?.get('x-csrf-token');
      if (!csrfToken) {
        throw new Error('CSRF token not returned by S/4HANA');
      }
      console.log('[Mass Change] CSRF token obtained:', csrfToken);

      // 2. Build batch multipart payload following Postman template
      const batchPayload = buildBatchPayload(filters, fieldsToUpdate);
      
      console.log('[Mass Change] Batch payload constructed:');
      console.log(batchPayload);

      // 3. Send batch request to S/4HANA with CSRF token
      const response = await s4Service.send({
        method: 'POST',
        path: '/$batch?sap-client=200',
        headers: {
          'Content-Type': 'multipart/mixed; boundary=batch_Test01',
          'Accept': 'application/json',
          'X-CSRF-Token': csrfToken
        },
        data: batchPayload
      });

      console.log('[Mass Change] S/4HANA response:', JSON.stringify(response, null, 2));

      // 3. Return success status to Joule
      return {
        ID: cds.utils.uuid(),
        status: 'JOB_SCHEDULED',
        jobName: 'Mass Field Update from Joule',
        timestamp: new Date().toISOString(),
        message: 'Job scheduled successfully. Check status in Manage Sales Documents (F4546) app.',
        fioriAppLink: '/sap/bc/ui5_ui5/sap/f4546/index.html' // Link to Fiori app
      };

    } catch (error) {
      console.error('[Mass Change] Error occurred:', error);
      
      // Return error status to Joule
      return {
        ID: cds.utils.uuid(),
        status: 'ERROR',
        jobName: 'Mass Field Update from Joule',
        timestamp: new Date().toISOString(),
        message: `Failed to schedule job: ${error.message || 'Unknown error'}`,
        fioriAppLink: ''
      };
    }
  });

});

/**
 * Builds batch OData multipart payload following exact Postman template
 * 
 * Architecture (from meeting):
 * - MERGE with "phantom order" (100001681) defines WHAT to change (fields)
 * - GET with dynamic filters defines WHICH orders to change
 * - S/4HANA combines both to execute mass update
 * 
 * @param {Object} filters - Selection criteria for orders
 * @param {Object} fields - Fields to update
 * @returns {string} Batch multipart payload
 */
function buildBatchPayload(filters, fields) {
  
  // Build dynamic GET query with filters
  const getQuery = buildGetQuery(filters);
  
  // Template from docs/postman.md - exact boundaries and headers
  // Note: Using template literals for proper variable interpolation
  const payload = `--batch_Test01
Content-Type: multipart/mixed; boundary=changeset_Ugo1

--changeset_Ugo1
Content-Type: application/http
Content-Transfer-Encoding: binary

MERGE C_RFM_MaSaDoEditSlsOrdItm(SalesOrder='100001681',SalesOrderItem='000010')?sap-client=110 HTTP/1.1
sap-contextid-accept: header
Accept: application/json
Accept-Language: en
DataServiceVersion: 2.0
MaxDataServiceVersion: 2.0
X-Requested-With: XMLHttpRequest
Content-Type: application/json
sap-message-scope: BusinessObject

{
    "RequirementSegment": "${fields.RequirementSegment}",
    "Plant": "${fields.Plant}",
    "StorageLocation": "${fields.StorageLocation}",
    "RFM_SD_ApplJobAction": "01",
    "InternalComment": "Mass Field Update from Joule",
    "SalesOrdItemIsSelected": "X",
    "SalesOrdItemsAreSelected": "X"
}
--changeset_Ugo1--

--batch_Test01
Content-Type: application/http
Content-Transfer-Encoding: binary

${getQuery}

--batch_Test01--
`;

  return payload;
}

/**
 * Builds dynamic GET query with URL-encoded filters
 * This determines WHICH orders will be modified
 * 
 * @param {Object} filters - Selection criteria
 * @returns {string} GET query part of batch
 */
function buildGetQuery(filters) {
  // URL-encode special characters for OData query
  const material = encodeURIComponent(filters.materialStartsWith);
  const plant = encodeURIComponent(filters.plant);
  const salesOrg = encodeURIComponent(filters.salesOrg);
  const date = encodeURIComponent(filters.creationDate);
  
  // Build GET request following Postman template
  return `GET C_RFM_MaSaDoEditSlsOrdItm?sap-client=200&$top=1&$filter=startswith(Material,%27${material}%27)%20and%20Plant%20eq%20%27${plant}%27%20and%20SalesDocumentDate%20eq%20datetime%27${date}T00%3a00%3a00%27%20and%20SalesOrganization%20eq%20%27${salesOrg}%27 HTTP/1.1
sap-cancel-on-close: true
sap-contextid-accept: header
Accept: application/json
Accept-Language: en
DataServiceVersion: 2.0
MaxDataServiceVersion: 2.0
X-Requested-With: XMLHttpRequest
sap-message-scope: BusinessObject`;
}
