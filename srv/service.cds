using { cuid, managed } from '@sap/cds/common';

/**
 * Mass Change Service for S/4HANA Sales Orders
 * Proxy service that converts Joule JSON requests to S/4HANA batch OData
 */
service MassChangeService {
  
  /**
   * Simple READ entity for testing connectivity (like boss's project)
   * Public endpoint - no auth required for testing
   */
  @requires: 'any'
  entity ConnectivityTest {
    key id      : Integer;
    status      : String;
    message     : String;
    timestamp   : String;
  }
  
  /**
   * Test action to compare S/4HANA endpoints
   */
  action testS4Endpoints() returns {
    timestamp: String;
    results: array of {
      endpoint: String;
      status: String;
      statusCode: Integer;
      contentLength: Integer;
      preview: String;
      error: String;
    };
    recommendation: String;
  };
  
  /**
   * Main action called by Joule to schedule mass change (ANDATA)
   * Receives filters to select orders and fields to update
   */
  
  action scheduleMassChange(
    filters: Filters,
    fieldsToUpdate: FieldsToUpdate
  ) returns OperationStatus;

  /**
   * Reversal action to restore original values (RITORNO)
   * Returns orders to initial state for testing
   */
  action reverseMassChange(
    filters: Filters
  ) returns OperationStatus;

  /**
   * Read action to verify applied changes
   * Retrieves current values of orders matching filters
   */
  action readOrders(
    filters: Filters
  ) returns {
    timestamp: String;
    count: Integer;
    orders: array of {
      SalesOrder: String;
      SalesOrderItem: String;
      Material: String;
      RequirementSegment: String;
      Plant: String;
      StorageLocation: String;
      SalesOrganization: String;
      SalesDocumentDate: String;
    };
  };



  /**
   * Filters for selecting sales orders to modify
   */
  type Filters {
    materialStartsWith : String;  // Material code prefix (e.g., "J01AA0119J35002001")
    plant              : String;  // Plant code (e.g., "142A")
    salesOrg           : String;  // Sales organization (e.g., "142")
    creationDate       : Date;    // Document creation date
  }

  /**
   * Fields to update in selected sales orders
   */
  type FieldsToUpdate {
    RequirementSegment : String;  // Requirement segment (e.g., "PPCOMFR")
    Plant              : String;  // New plant (e.g., "140A")
    StorageLocation    : String;  // New storage location (e.g., "ROD")
  }

  /**
   * Response status returned to Joule
   */
  type OperationStatus {
    ID          : UUID;
    status      : String;   // "JOB_SCHEDULED" or "ERROR"
    jobName     : String;   // Job name for tracking
    timestamp   : DateTime; // When the request was processed
    message     : String;   // Details for user/Joule
    fioriAppLink: String;   // Link to Manage Sales Documents app (F4546)
  }
}
