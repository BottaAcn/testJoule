Perfetto Lorenzo, andiamo **dritti al punto**:  
sulla base delle informazioni che hai, **possiamo tracciare il percorso operativo esatto — passo‑passo — per iniziare a costruire il servizio CAP su BTP**, dato che la **destination è già presente**.

Questa guida è pensata esattamente per il tuo scenario attuale **(SB4 via Cloud Connector, destination già configurata, batch non supportato da Joule)**.

***

# ✅ **FASE 0 — Verifica unica necessaria (prima di iniziare)**

La destination BTP che userai deve avere:

*   **ProxyType: OnPremise**
*   **URL: <https://sb4-od-44300>** (virtual host del Cloud Connector)
*   **sap-client = 200**
*   **Authentication: Basic** *oppure* **OAuth2ClientCredentials**

Se questo è già così → **si parte**.

***

# 🚀 **FASE 1 — Creare il progetto CAP (Node.js)**

1.  Apri il tuo terminale **Cloud Foundry** (BAS oppure locale).
2.  Esegui:

```bash
npm install -g @sap/cds-dk
cd <tua-cartella>
cds init mass-change-proxy
```

3.  Entra nel progetto:

```bash
cd mass-change-proxy
```

4.  Aggiungi il server Node:

```bash
cds add nodejs
```

A questo punto hai un progetto CAP Node.js vuoto, pronto.

***

# 🚀 **FASE 2 — Creare il servizio API che Joule chiamerà**

1.  Nel progetto, crea questo file:

`/srv/mass-change-service.cds`

Contenuto:

```cds
using { cuid } from '@sap/cds/common';

service MassChangeService {
  @readonly entity OperationStatus {
    key ID     : UUID;
    status     : String;
    jobName    : String;
    timestamp  : DateTime;
  }

  @impl action scheduleMassChange(
    filters: Filters,
    fieldsToUpdate: FieldsToUpdate
  ) returns OperationStatus;

  type Filters : {
    materialStartsWith : String;
    plant              : String;
    salesOrg           : String;
    creationDate       : Date;
  };

  type FieldsToUpdate : {
    RequirementSegment : String;
    Plant              : String;
    StorageLocation    : String;
  };
}
```

Questa è l’API che Joule chiamerà.

***

# 🚀 **FASE 3 — Implementazione dell’action (batch builder proxy)**

Crea:

`/srv/mass-change-service.js`

Contenuto base:

```js
const cds = require('@sap/cds');
const axios = require('axios');

module.exports = cds.service.impl(async function () {

  const destination = await cds.connect.to('sb4-odata'); // ← nome della tua Destination

  this.on('scheduleMassChange', async (req) => {

    const { filters, fieldsToUpdate } = req.data;

    // 1) componi la GET di selezione
    const selectionGET = buildSelectionGET(filters);

    // 2) componi il batch multipart
    const batchPayload = buildBatchPayload(filters, fieldsToUpdate);

    // 3) chiama l’endpoint batch
    const response = await destination.send({
      method: 'POST',
      path: '/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$batch?sap-client=200',
      headers: {
        'Content-Type': 'multipart/mixed; boundary=batch_Test01',
        'Accept': 'application/json'
      },
      data: batchPayload
    });

    // 4) restituisci ad Joule un “job scheduled”
    return {
      ID: cds.utils.uuid(),
      status: "JOB_SCHEDULED",
      jobName: "MassFieldUpdate"
    };
  });

});
```

**Nota:**  
È qui che poi aggiungeremo le funzioni:

*   `buildSelectionGET(filters)`
*   `buildBatchPayload(filters, fieldsToUpdate)`

Ma puoi procedere anche senza averle già definite: CAP compilerà comunque.

***

# 🚀 **FASE 4 — Creazione delle funzioni helper per il batch ($batch)**

Aggiungi in `/srv/batch-builder.js`:

```js
module.exports.buildSelectionGET = function (filters) {
  return `GET C_RFM_MaSaDoEditSlsOrdItm?sap-client=200&$top=1&$filter=startswith(Material,'${filters.materialStartsWith}')
  and Plant eq '${filters.plant}'
  and SalesOrganization eq '${filters.salesOrg}'
  and SalesDocumentDate eq datetime'${filters.creationDate}T00:00:00' HTTP/1.1`;
};

module.exports.buildBatchPayload = function (filters, fields) {

  return `
--batch_Test01
Content-Type: multipart/mixed; boundary=changeset_Ugo1

--changeset_Ugo1
Content-Type: application/http
Content-Transfer-Encoding: binary

MERGE C_RFM_MaSaDoEditSlsOrdItm(SalesOrder='100001681',SalesOrderItem='000010')?sap-client=200 HTTP/1.1
Content-Type: application/json

{
  "RequirementSegment": "${fields.RequirementSegment}",
  "Plant": "${fields.Plant}",
  "StorageLocation": "${fields.StorageLocation}",
  "RFM_SD_ApplJobAction": "01",
  "InternalComment": "Mass Update from Proxy",
  "SalesOrdItemIsSelected": "X",
  "SalesOrdItemsAreSelected": "X"
}
--changeset_Ugo1--

--batch_Test01
Content-Type: application/http
Content-Transfer-Encoding: binary

${module.exports.buildSelectionGET(filters)}

--batch_Test01--
`;
};
```

Questo è un **template minimale**: lo affiniamo dopo.

***

# 🚀 **FASE 5 — Aggiungere la Destination al progetto CAP**

Nel file:  
`default-env.json` (o nel service binding CF):

```json
{
  "destinations": [
    {
      "name": "sb4-odata",
      "forwardAuthToken": true
    }
  ]
}
```

Il binding reale lo prende da BTP.

***

# 🚀 **FASE 6 — Deploy su Cloud Foundry**

Da terminale:

```bash
cds build --production
cf push
```

L’app partirà esponendo l’endpoint:

    POST /mass-change-service/scheduleMassChange

Questa è l’API che Joule chiamerà.

***

# 🚀 **FASE 7 — Test minimo via Postman**

Prova subito:

    POST <app-url>/mass-change-service/scheduleMassChange

Body:

```json
{
  "filters": {
    "materialStartsWith": "J01AA",
    "plant": "142A",
    "salesOrg": "142",
    "creationDate": "2026-01-13"
  },
  "fieldsToUpdate": {
    "RequirementSegment": "PPCOMFR",
    "Plant": "140A",
    "StorageLocation": "ROD"
  }
}
```

Se funziona → ricevi:

```json
{
  "status": "JOB_SCHEDULED",
  "jobName": "MassFieldUpdate"
}
```

***

# 🚀 **FASE 8 — Collegamento Joule → CAP**

Da Joule:

1.  Crea Action “Mass Change (Custom Proxy)”
2.  Endpoint:  
    `POST /mass-change-service/scheduleMassChange`
3.  Parametri esposti = filters + fieldsToUpdate
4.  Risposta mappata nella tile/skill

Ed è finita.

***

# 🎯 **Hai TUTTO per iniziare subito**

La destination è già pronta → quindi puoi partire dalla **FASE 1**.

***
