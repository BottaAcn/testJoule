Ciao Riccardo e Dario,
come concordato ieri mattina, vi invio i dettagli per effettuare una chiamata al servizio di modifica massiva ordini di vendita (RFM_MANAGE_SALES_ORDERS_SRV) che abbiamo testato con successo da Postman.
La chiamata punta al sistema Sandbox (SB4), mandante 200, e prevede di modificare gli ordini di vendita estratti con i seguenti filtri (sono i tre ordini di vendita 100000625, 100000626 e 100000627):

•	Sales Organization: 142
•	Material: J01AA0119J35002001*
•	Plant: 142A
•	Document date: 13.01.2026

Impostando i seguenti dati

•	RequirementSegment: PPCOMFR
•	Plant: 140A
•	StorageLocation: ROD

L’url è il seguente: https://vhotbsb4ci.rise.otb.net:44300/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$batch?sap-client=200 

E il payload del body: 

--batch_Test01
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
    "RequirementSegment": "PPCOMFR",
    "Plant": "140A",
    "StorageLocation": "ROD",
    "RFM_SD_ApplJobAction": "01",
    "InternalComment": "Mass Field Update-ANDATA",
    "SalesOrdItemIsSelected": "X",
    "SalesOrdItemsAreSelected": "X"
}
--changeset_Ugo1--

--batch_Test01
Content-Type: application/http
Content-Transfer-Encoding: binary

GET C_RFM_MaSaDoEditSlsOrdItm?sap-client=200&$top=1&$filter=startswith(Material,%27J01AA0119J35002001%27)%20and%20Plant%20eq%20%27142A%27%20and%20SalesDocumentDate%20eq%20datetime%272026-01-13T00%3a00%3a00%27%20and%20SalesOrganization%20eq%20%27142%27 HTTP/1.1
sap-cancel-on-close: true
sap-contextid-accept: header
Accept: application/json
Accept-Language: en
DataServiceVersion: 2.0
MaxDataServiceVersion: 2.0
X-Requested-With: XMLHttpRequest
sap-message-scope: BusinessObject

--batch_Test01--

Abbiamo anche predisposto la chiamata per riportare i dati alla situazione iniziale in modo tale che i test possano essere ripetuti quante volte si vuole.
L’url è lo stesso: https://vhotbsb4ci.rise.otb.net:44300/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$batch?sap-client=200 

Ed il payload del body:

--batch_Test01
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
    "RequirementSegment": "PPCOM99",
    "Plant": "142A",
    "StorageLocation": "AFS",
    "RFM_SD_ApplJobAction": "01",
    "InternalComment": "Mass Field Update RITORNO",
    "SalesOrdItemIsSelected": "X",
    "SalesOrdItemsAreSelected": "X"
}
--changeset_Ugo1--

--batch_Test01
Content-Type: application/http
Content-Transfer-Encoding: binary

GET C_RFM_MaSaDoEditSlsOrdItm?sap-client=200&$top=1&$filter=startswith(Material,%27J01AA0119J35002001%27)%20and%20Plant%20eq%20%27140A%27%20and%20SalesDocumentDate%20eq%20datetime%272026-01-13T00%3a00%3a00%27 HTTP/1.1
sap-cancel-on-close: true
sap-contextid-accept: header
Accept: application/json
Accept-Language: en
DataServiceVersion: 2.0
MaxDataServiceVersion: 2.0
X-Requested-With: XMLHttpRequest
sap-message-scope: BusinessObject

--batch_Test01--
