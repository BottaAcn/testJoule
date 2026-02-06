const cds = require('@sap/cds');

/**
 * Implementation of MassChangeService
 * Converts Joule JSON requests to S/4HANA batch OData multipart
 */
module.exports = cds.service.impl(async function () {

  // Lazy loading approach (like boss's project)
  let OnPremService = undefined;

  /**
   * READ handler for ConnectivityTest entity
   * Simple test to verify S/4HANA connectivity
   */
  this.on(['READ'], 'ConnectivityTest', async (req) => {
    // Initialize connection on first use
    if (!OnPremService) {
      OnPremService = await cds.connect.to('OnPremService');
      console.log('[ConnectivityTest] Connected to S4HANA via OnPremService');
    }

    try {
      // Test: call service root with metadata request
      console.log('[ConnectivityTest] Testing S/4HANA connectivity...');
      const res = await OnPremService.get('/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$metadata?sap-client=200');
      
      return [{
        id: 1,
        status: 'SUCCESS',
        message: `Connected to S/4HANA successfully! Metadata size: ${String(res).length} bytes`,
        timestamp: new Date().toISOString()
      }];
    } catch (err) {
      console.error('[ConnectivityTest] Error:', err);
      return [{
        id: 1,
        status: 'ERROR',
        message: `Connection failed: ${err.message || err}`,
        timestamp: new Date().toISOString()
      }];
    }
  });

  /**
   * Test endpoint to compare two S/4HANA systems
   * Tests both internal (OnPremise) and RISE endpoints
   */
  this.on('testS4Endpoints', async (req) => {
    // Initialize connection on first use (lazy loading)
    if (!OnPremService) {
      OnPremService = await cds.connect.to('OnPremService');
      console.log('[Test] Connected to S4HANA via OnPremService');
    }
    
    const results = [];
    
    // Test 1: Internal S/4HANA via Cloud Connector (destination S4HANA_PCE_SSO)
    try {
      console.log('[Test] Testing internal S4 via destination S4HANA_PCE_SSO...');
      const internalResponse = await OnPremService.send({
        method: 'GET',
        path: '/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$metadata?sap-client=200',
        headers: { 'Accept': 'application/xml' }
      });
      
      results.push({
        endpoint: 'S4HANA_PCE_SSO (s4-sb4:44380 via Cloud Connector)',
        status: 'SUCCESS',
        statusCode: 200,
        contentLength: String(internalResponse).length,
        preview: String(internalResponse).substring(0, 200)
      });
    } catch (error) {
      results.push({
        endpoint: 'S4HANA_PCE_SSO (s4-sb4:44380 via Cloud Connector)',
        status: 'FAILED',
        error: error.message
      });
    }
    
    // Test 2: RISE S/4HANA via direct HTTP call (no destination)
    try {
      console.log('[Test] Testing RISE S4 via direct HTTP call...');
      const https = require('https');
      
      const riseResponse = await new Promise((resolve, reject) => {
        const options = {
          hostname: 'vhotbsb4ci.rise.otb.net',
          port: 44300,
          path: '/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$metadata?sap-client=200',
          method: 'GET',
          headers: {
            'Authorization': 'Basic ' + Buffer.from('JOULE_ADMIN:Diesel_2025_978625!').toString('base64'),
            'Accept': 'application/xml'
          },
          rejectUnauthorized: false // Accept self-signed certs
        };
        
        const req = https.request(options, (res) => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => {
            if (res.statusCode === 200) {
              resolve({ statusCode: res.statusCode, data });
            } else {
              reject(new Error(`HTTP ${res.statusCode}: ${data.substring(0, 200)}`));
            }
          });
        });
        
        req.on('error', reject);
        req.setTimeout(10000, () => {
          req.destroy();
          reject(new Error('Request timeout after 10s'));
        });
        req.end();
      });
      
      results.push({
        endpoint: 'RISE (vhotbsb4ci.rise.otb.net:44300 direct HTTP)',
        status: 'SUCCESS',
        statusCode: riseResponse.statusCode,
        contentLength: riseResponse.data.length,
        preview: riseResponse.data.substring(0, 200)
      });
    } catch (error) {
      results.push({
        endpoint: 'RISE (vhotbsb4ci.rise.otb.net:44300 direct HTTP)',
        status: 'FAILED',
        error: error.message
      });
    }
    
    return {
      timestamp: new Date().toISOString(),
      results: results,
      recommendation: results.some(r => r.status === 'SUCCESS') 
        ? 'At least one endpoint is working!' 
        : 'Both endpoints failed - check configuration'
    };
  });

  /**
   * Handler for scheduleMassChange action
   * Receives filters and fields from Joule, builds batch payload, sends to S/4HANA
   */
  this.on('scheduleMassChange', async (req) => {
    // Initialize connection on first use (lazy loading)
    if (!OnPremService) {
      OnPremService = await cds.connect.to('OnPremService');
      console.log('[Mass Change] Connected to S4HANA via OnPremService');
    }
    
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
      
      // Use SAP Cloud SDK to get access to response headers
      const { executeHttpRequest } = require('@sap-cloud-sdk/http-client');
      const csrfResponse = await executeHttpRequest(
        { destinationName: 'S4HANA_PCE_SSO' },
        {
          method: 'get',
          url: '/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/',
          headers: {
            'X-CSRF-Token': 'Fetch',
            'Accept': 'application/json'
          }
        }
      );
      
      console.log('[Mass Change] CSRF response headers:', csrfResponse.headers);
      const csrfToken = csrfResponse.headers['x-csrf-token'];
      const cookies = csrfResponse.headers['set-cookie']; // Extract session cookies!
      if (!csrfToken) {
        console.error('[Mass Change] No CSRF token in headers:', Object.keys(csrfResponse.headers));
        throw new Error('CSRF token not returned by S/4HANA');
      }
      console.log('[Mass Change] CSRF token obtained:', csrfToken);
      console.log('[Mass Change] Session cookies:', cookies);

      // 2. Build batch multipart payload following Postman template
      const batchPayload = buildBatchPayload(filters, fieldsToUpdate);
      
      console.log('[Mass Change] Batch payload length:', batchPayload.length, 'bytes');
      console.log('[Mass Change] Payload has CRLF:', batchPayload.includes('\r\n') ? 'YES' : 'NO');
      // Write payload to temp file for debugging (will log file path)
      const fs = require('fs');
      const tmpFile = `/tmp/batch_payload_${Date.now()}.txt`;
      fs.writeFileSync(tmpFile, batchPayload, 'utf8');
      console.log('[Mass Change] Payload written to:', tmpFile);
      console.log('[Mass Change] Sending batch with CSRF token:', csrfToken);

      // 3. Send batch request to S/4HANA with CSRF token AND session cookies using SAP Cloud SDK
      const batchResponse = await executeHttpRequest(
        { destinationName: 'S4HANA_PCE_SSO' },
        {
          method: 'post',
          url: '/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$batch?sap-client=200',
          headers: {
            'Content-Type': 'multipart/mixed; boundary=batch_Test01',
            'Accept': 'application/json',
            'X-CSRF-Token': csrfToken,
            'Cookie': cookies ? cookies.join('; ') : '' // Send session cookies back!
          },
          data: batchPayload
        }
      );

      console.log('[Mass Change] S/4HANA batch response status:', batchResponse.status);
      console.log('[Mass Change] S/4HANA batch response headers:', JSON.stringify(batchResponse.headers, null, 2));
      console.log('[Mass Change] S/4HANA batch response data:', JSON.stringify(batchResponse.data, null, 2));

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
      console.error('[Mass Change] Error occurred:', error.message);
      if (error.response) {
        console.error('[Mass Change] Error status:', error.response.status);
        console.error('[Mass Change] Error headers:', JSON.stringify(error.response.headers, null, 2));
        console.error('[Mass Change] Error body:', JSON.stringify(error.response.data, null, 2)); // Pretty print with indentation
      }
      
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

  /**
   * RITORNO action - Reverses mass change to restore original values
   * Uses fixed RITORNO values from Postman documentation
   */
  this.on('reverseMassChange', async (req) => {
    // Initialize connection on first use
    if (!OnPremService) {
      OnPremService = await cds.connect.to('OnPremService');
      console.log('[RITORNO] Connected to S4HANA via OnPremService');
    }
    
    const { filters } = req.data;
    
    console.log('[RITORNO] Reversal request received:', JSON.stringify(req.data, null, 2));

    if (!filters) {
      return {
        ID: cds.utils.uuid(),
        status: 'ERROR',
        jobName: 'Mass Field Update RITORNO',
        timestamp: new Date().toISOString(),
        message: 'Missing required parameter: filters',
        fioriAppLink: ''
      };
    }

    try {
      // Fixed RITORNO values from postman.md
      const riturnoFields = {
        RequirementSegment: 'PPCOM99',
        Plant: '142A',
        StorageLocation: 'AFS'
      };

      // 1. Fetch CSRF token
      console.log('[RITORNO] Fetching CSRF token...');
      const { executeHttpRequest } = require('@sap-cloud-sdk/http-client');
      const csrfResponse = await executeHttpRequest(
        { destinationName: 'S4HANA_PCE_SSO' },
        {
          method: 'get',
          url: '/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/',
          headers: {
            'X-CSRF-Token': 'Fetch',
            'Accept': 'application/json'
          }
        }
      );
      
      const csrfToken = csrfResponse.headers['x-csrf-token'];
      const cookies = csrfResponse.headers['set-cookie'];
      if (!csrfToken) {
        throw new Error('CSRF token not returned by S/4HANA');
      }
      console.log('[RITORNO] CSRF token obtained:', csrfToken);

      // 2. Build batch payload with RITORNO values
      // Note: GET filter uses Plant=140A (after ANDATA change) as per postman.md
      const riturnoFilters = { ...filters, plant: '140A' }; // Search in changed plant
      const batchPayload = buildBatchPayload(riturnoFilters, riturnoFields);
      
      console.log('[RITORNO] Batch payload ready, length:', batchPayload.length, 'bytes');

      // 3. Send batch request
      const batchResponse = await executeHttpRequest(
        { destinationName: 'S4HANA_PCE_SSO' },
        {
          method: 'post',
          url: '/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$batch?sap-client=200',
          headers: {
            'Content-Type': 'multipart/mixed; boundary=batch_Test01',
            'Accept': 'application/json',
            'X-CSRF-Token': csrfToken,
            'Cookie': cookies ? cookies.join('; ') : ''
          },
          data: batchPayload
        }
      );

      console.log('[RITORNO] S/4HANA response status:', batchResponse.status);
      console.log('[RITORNO] Response data:', JSON.stringify(batchResponse.data, null, 2));

      return {
        ID: cds.utils.uuid(),
        status: 'JOB_SCHEDULED',
        jobName: 'Mass Field Update RITORNO',
        timestamp: new Date().toISOString(),
        message: 'Reversal job scheduled successfully. Orders restored to original values.',
        fioriAppLink: '/sap/bc/ui5_ui5/sap/f4546/index.html'
      };

    } catch (error) {
      console.error('[RITORNO] Error occurred:', error.message);
      if (error.response) {
        console.error('[RITORNO] Error status:', error.response.status);
        console.error('[RITORNO] Error body:', JSON.stringify(error.response.data, null, 2));
      }
      
      return {
        ID: cds.utils.uuid(),
        status: 'ERROR',
        jobName: 'Mass Field Update RITORNO',
        timestamp: new Date().toISOString(),
        message: `Failed to schedule reversal: ${error.message || 'Unknown error'}`,
        fioriAppLink: ''
      };
    }
  });

  /**
   * READ action - Retrieves orders matching filters to verify changes
   * Uses GET query to read current values from S/4HANA
   */
  this.on('readOrders', async (req) => {
    // Initialize connection on first use
    if (!OnPremService) {
      OnPremService = await cds.connect.to('OnPremService');
      console.log('[READ] Connected to S4HANA via OnPremService');
    }
    
    const { filters } = req.data;
    
    console.log('[READ] Read request received:', JSON.stringify(req.data, null, 2));

    if (!filters) {
      return {
        timestamp: new Date().toISOString(),
        count: 0,
        orders: []
      };
    }

    try {
      // Build OData query with filters
      const material = encodeURIComponent(filters.materialStartsWith);
      const plant = encodeURIComponent(filters.plant);
      const salesOrg = encodeURIComponent(filters.salesOrg);
      const date = encodeURIComponent(filters.creationDate);
      
      const filterQuery = `startswith(Material,'${material}') and Plant eq '${plant}' and SalesDocumentDate eq datetime'${date}T00:00:00' and SalesOrganization eq '${salesOrg}'`;
      const encodedFilter = encodeURIComponent(filterQuery);
      
      console.log('[READ] Filter query:', filterQuery);

      // Execute GET request
      const response = await OnPremService.send({
        method: 'GET',
        path: `/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/C_RFM_MaSaDoEditSlsOrdItm?sap-client=200&$filter=${encodedFilter}&$select=SalesOrder,SalesOrderItem,Material,RequirementSegment,Plant,StorageLocation,SalesOrganization,SalesDocumentDate`,
        headers: { 
          'Accept': 'application/json'
        }
      });

      console.log('[READ] Response received, parsing results...');
      
      // Parse OData response
      const results = response.d?.results || [];
      
      console.log('[READ] Found', results.length, 'orders');

      return {
        timestamp: new Date().toISOString(),
        count: results.length,
        orders: results.map(order => ({
          SalesOrder: order.SalesOrder,
          SalesOrderItem: order.SalesOrderItem,
          Material: order.Material,
          RequirementSegment: order.RequirementSegment,
          Plant: order.Plant,
          StorageLocation: order.StorageLocation,
          SalesOrganization: order.SalesOrganization,
          SalesDocumentDate: order.SalesDocumentDate
        }))
      };

    } catch (error) {
      console.error('[READ] Error occurred:', error.message);
      if (error.response) {
        console.error('[READ] Error status:', error.response.status);
        console.error('[READ] Error body:', JSON.stringify(error.response.data, null, 2));
      }
      
      return {
        timestamp: new Date().toISOString(),
        count: 0,
        orders: [],
        error: error.message
      };
    }
  });

});

/**
 * Builds batch OData multipart payload following exact Postman template
 * Based on working Python payload - includes Host and Content-Length headers
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
  
  // Build JSON body for MERGE
  const mergeBody = JSON.stringify({
    "RequirementSegment": fields.RequirementSegment,
    "Plant": fields.Plant,
    "StorageLocation": fields.StorageLocation,
    "RFM_SD_ApplJobAction": "01",
    "InternalComment": "Mass Field Update from Joule",
    "SalesOrdItemIsSelected": "X",
    "SalesOrdItemsAreSelected": "X"
  });
  
  // Build GET filter query
  const material = filters.materialStartsWith;
  const plant = filters.plant;
  const salesOrg = filters.salesOrg;
  const date = filters.creationDate;
  const getFilter = `startswith(Material,%27${material}%27)%20and%20Plant%20eq%20%27${plant}%27%20and%20SalesDocumentDate%20eq%20datetime%27${date}T00%3a00%3a00%27%20and%20SalesOrganization%20eq%20%27${salesOrg}%27`;
  
  // Host header value (internal S/4HANA hostname from Destination)
  const HOST = "s4-sb4:44380";
  
  // Build complete batch payload with CRLF line endings
  // CRITICAL: Host and Content-Length headers are REQUIRED for S/4HANA
  const payload = [
    // Changeset part (wraps write operations like MERGE)
    '--batch_Test01',
    'Content-Type: multipart/mixed; boundary=changeset_Ugo1',
    '',
    '--changeset_Ugo1',
    'Content-Type: application/http',
    'Content-Transfer-Encoding: binary',
    '',
    'MERGE C_RFM_MaSaDoEditSlsOrdItm(SalesOrder=\'100001681\',SalesOrderItem=\'000010\')?sap-client=200 HTTP/1.1',
    `Host: ${HOST}`,  // CRITICAL: Host header required
    'Content-Type: application/json',
    `Content-Length: ${mergeBody.length}`,  // CRITICAL: Content-Length required for body
    'Accept: application/json',
    '',  // Blank line before body
    mergeBody,
    '--changeset_Ugo1--',
    '',
    // GET part (read operation, outside changeset)
    '--batch_Test01',
    'Content-Type: application/http',
    'Content-Transfer-Encoding: binary',
    '',
    `GET C_RFM_MaSaDoEditSlsOrdItm?$top=1&sap-client=200&$filter=${getFilter} HTTP/1.1`,
    `Host: ${HOST}`,  // CRITICAL: Host header required for GET too
    'Accept: application/json',
    '',
    '',  // CRITICAL: Two blank lines after GET headers (one closes headers, one for no body)
    '--batch_Test01--'
  ].join('\r\n');  // CRITICAL: Use CRLF as per OData spec

  return payload;
}
