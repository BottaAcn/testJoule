## 🚀 **Guida Completa BAS - Step by Step**

### **1. Apri il progetto clonato**
```bash
# Nel terminale BAS
cd /home/user/projects/testJoule  # (o dove hai clonato)
```
**Oppure:** File → Open Folder → Seleziona testJoule

---

### **2. Installa dipendenze npm**
```bash
npm install
```
Attendi completamento (installerà `@sap-cloud-sdk/*` e altre dipendenze)

---

### **3. Verifica destination S4H su BTP Cockpit**
```
BTP Cockpit → Subaccount → Connectivity → Destinations → S4H
```
✅ Verifica che esista con:
- User: `ESTUSER30`
- Password configurata
- URL: `https://saps4hana.expertsoft.in:8086`

---

### **4. Login Cloud Foundry**
```bash
cf login
```
- API endpoint: (quello del tuo BTP)
- Seleziona **org** e **space** (es. `Joule_S4_SB4`)

---

### **5. Build MTAR**
```bash
mbt build
```
Genera `mta_archives/testJoule_1.0.0.mtar`

---

### **6. Deploy su Cloud Foundry**
```bash
cf deploy mta_archives/testJoule_1.0.0.mtar
```
Attendi deploy (~5-10 min)

---

### **7. Verifica deployment**
```bash
# Verifica app in esecuzione
cf apps

# Verifica binding destination
cf env testJoule-srv
```
Cerca `VCAP_SERVICES.destination` nell'output

---

### **8. Ottieni URL applicazione**
```bash
cf app testJoule-srv
```
Copia l'URL (es. `https://testJoule-srv-...cfapps.eu10.hana.ondemand.com`)

---

### **9. Test endpoint con Postman**
```
POST https://<app-url>/odata/v4/mass-change/scheduleMassChange

Headers:
  Content-Type: application/json

Body:
{
  "filters": {
    "materialStartsWith": "J01AA0119J35002001",
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

---

### **10. Debug se serve**
```bash
# Visualizza log in tempo reale
cf logs testJoule-srv

# Log recenti
cf logs testJoule-srv --recent
```

---

## 📋 **Quick Reference:**
```bash
cd testJoule
npm install
cf login
mbt build
cf deploy mta_archives/*.mtar
cf apps
cf logs testJoule-srv --recent
```

**Inizia da `npm install`!** 🚀