# The Rizzlers
-Mike, Mathias, Esben og Johan
# Hotel Kong Arthur – Dataanalyse- og Microservice-system

## 1. Projektets formål og kontekst

Hotel Kong Arthur-projektet er udviklet som et microservice-baseret analysesystem, der samler og visualiserer hotellets nøgletal på tværs af afdelinger.
Systemet henter, bearbejder og præsenterer data om gæster, reservationer, værelsestyper og baromsætning gennem et samlet Streamlit-dashboard.

Formålet er at demonstrere, hvordan et moderne hotel kan anvende distribueret softwarearkitektur og datadrevet beslutningsstøtte til at optimere forretningen.
Projektet er både et teknisk bevis på korrekt mikroservice-integration (via Flask + Docker + API Gateway) og et eksempel på real-time business intelligence for ledelsen.

---

## 2. Arkitektur-overblik

Systemet består af seks selvstændige services, der tilsammen danner et fleksibelt og skalerbart økosystem.

| Komponent               | Teknologi                                    | Rolle                                                                                                                           |
| ----------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Streamlit Frontend**  | Python (Streamlit, Altair, Pandas)           | Visualiserer KPI’er, sæsondata, heatmaps og gæstefordelinger i real time.                                                       |
| **API Gateway**         | Flask                                        | Central indgang for frontend-kald. Proxy’er forespørgsler til de underliggende services og håndterer timeout- og error-styring. |
| **Analytics Service**   | Flask + Pandas                               | Samler nøgletal på tværs af Room, Bar, Guest og Reservation-services. Beregner samlede KPI’er og videresender dem til Gateway.  |
| **Room Service**        | Flask + SQLite                               | Indeholder alle værelser og reservationer. Tilbyder endpoints for omsætning pr. værelsestype, sæson og land.                    |
| **Guest Service**       | Flask + Pandas + Requests                    | Kombinerer gæstedata med room-data via HTTP-kald og udleder indsigter som "by country", "by season" og "by country × roomtype". |
| **Reservation Service** | Flask + SQLite                               | Håndterer reservationsdata og leverer nøgletal som gennemsnitlig pris, varighed og månedlig omsætning.                          |
| **Bar Service**         | Flask + SQLite (drinks_menu_with_sales.xlsx) | Beregner omsætning, gennemsnitspris og top-produkter i baren.                                                                   |

Alle services kommunikerer via HTTP over et fælles Docker-netværk (`hotel_arthur_net`), og API Gateway fungerer som systemets offentlige adgangspunkt på port 8000.
Frontend-delen afvikles som selvstændig container på port 8501.

---

## 3. Teknologistak

| Lag                         | Teknologi / Bibliotek                                   | Anvendelse                                                 |
| --------------------------- | ------------------------------------------------------- | ---------------------------------------------------------- |
| **Backend (Microservices)** | Python 3.11 · Flask · Pandas · Requests                 | REST-API’er, databehandling og integration mellem services |
| **Frontend (Dashboard)**    | Streamlit · Altair · Pandas                             | Interaktive dashboards og grafer                           |
| **Database**                | SQLite (autogenereret fra CSV / XLSX-filer)             | Lokal, letvægtslagring for hver service                    |
| **Containere**              | Docker · Docker Compose                                 | Orkestrering af services og fælles netværk                 |
| **Datasæt**                 | NamesRoomsWithMonths4.csv · drinks_menu_with_sales.xlsx | Kildedata for hotel- og baromsætning                       |
| **Miljøhåndtering**         | requirements.txt · docker-volumes (`./data:/app/data`)  | Delte datafiler mellem containere                          |
| **Visualisering**           | Altair + Streamlit components                           | KPI-visninger, sæsongrafer og heatmaps                     |

Teknologierne er valgt for at vise en fuld end-to-end pipeline i Python, hvor alt fra datakilder til visualisering kører isoleret i containere, men stadig kommunikerer problemfrit via API-gatewayen.

---

Her kommer **Del 2 (README – punkterne 4-6)**, i ren Markdown og samme professionelle stil:

---

## 4. Sådan kører du projektet

### Krav

* Docker Desktop installeret og kørende
* Ingen aktive processer, der bruger port 8501 (Streamlit) eller 8000 (API Gateway)

### Installation og opstart

1. Klon repository’et:

   ```bash
   git clone <repo-url>
   cd Miniprojekt_HotelKongArthur
   ```
2. Byg og start alle services:

   ```bash
   docker-compose up --build
   ```
3. Når buildet er færdigt:

   * Streamlit Dashboard: [http://localhost:8501](http://localhost:8501)
   * API Gateway: [http://localhost:8000](http://localhost:8000)

### Hurtige kommandoer

| Handling                                   | Kommando                             |
| ------------------------------------------ | ------------------------------------ |
| Start alle containere (efter første build) | `docker-compose up`                  |
| Stop alle containere                       | `docker-compose down`                |
| Genbyg en enkelt service                   | `docker-compose build <servicenavn>` |
| Se logs for service                        | `docker-compose logs <servicenavn>`  |

**Bemærk:**
Første build kan tage tid, da alle images hentes og installeres.
Ved efterfølgende ændringer i kode behøves kun `--build` hvis Dockerfile eller requirements er opdateret.

---

## 5. Projektstruktur

```
📁 Miniprojekt_HotelKongArthur/
│
├── 📁 services/
│   ├── 📁 room/                →  room_service  (værelsesdata)
│   ├── 📁 guest/               →  guest_service (gæstedata & analyse)
│   ├── 📁 reservation/         →  reservation_service (bookinger)
│   ├── 📁 bar/                 →  bar_service (baromsætning)
│   └── 📁 analytics/           →  analytics_service (samler data på tværs)
│
├── 📁 frontend-streamlit/      →  Streamlit-frontend
│
├── 📁 data/                    →  Delte datakilder (.csv, .xlsx)
│   ├── NamesRoomsWithMonths4.csv
│   └── drinks_menu_with_sales.xlsx
│
├── 📄 docker-compose.yml       →  Samler alle services i ét netværk
├── 📄 README.md                →  Dokumentation (denne fil)
└── 📄 requirements.txt         →  Fælles afhængigheder
```

### Kort forklaring

* **services/**: indeholder hver sin Flask-applikation med egen database og endpoints
* **frontend-streamlit/**: kører dashboardet med KPI’er, grafer og interaktive filtre
* **data/**: mapper som delt volume (`./data:/app/data`) mellem alle containere
* **docker-compose.yml**: definerer netværk, porte, afhængigheder og build-steps

---

## 6. Datagrundlag

### Overblik

Projektet benytter to centrale datakilder:

| Fil                             | Indhold                                                                             | Anvendelse                                 |
| ------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------ |
| **NamesRoomsWithMonths4.csv**   | Værelses- og reservationsdata for hele året (priser, sæsoner, lande, værelsestyper) | Grundlag for room_service og guest_service |
| **drinks_menu_with_sales.xlsx** | Produkt- og salgstal fra hotellets bar                                              | Grundlag for bar_service                   |

Begge filer indlæses automatisk i hver service og konverteres til SQLite-databaser ved opstart.

### Databehandling

* **room_service**: beregner omsætning pr. land, værelsestype og sæson ud fra kolonnen `Price`.
* **guest_service**: henter room-data via HTTP og sammenknytter den med gæstelisten for at finde gennemsnitligt ophold og landefordeling.
* **reservation_service**: opsummerer reservationer og udleder månedlig omsætning.
* **bar_service**: konverterer Excel-data til SQLite og beregner kategoriomsætning og top-produkter.

### Konsistens

Alle services benytter de samme datakilder via Docker-volumes, så ændringer i `/data` synkroniseres mellem containere.
Revenue defineres som **direkte pris (`Price`)**, ikke `Price × Days Rented`, for at matche Tableau-beregningerne.

---

Her kommer **Del 3 (README – punkterne 7–9)**, fortsat i samme markdown-format og struktur:

---

## 7. Nøgletal og beregningslogik

Systemet genererer en række KPI’er (Key Performance Indicators), som danner grundlag for analyserne i dashboardet.
Beregningerne udføres i de respektive microservices og samles i **analytics_service**.

### Centrale KPI’er

| KPI                                | Beregning                                                    | Kilde               |
| ---------------------------------- | ------------------------------------------------------------ | ------------------- |
| **Total omsætning**                | Summering af revenue fra Room-, Bar- og Reservation-services | Analytics           |
| **Gns. dagspris (ADR)**            | Gennemsnitlig `price` pr. reservation                        | Reservation         |
| **Gns. ophold (dage)**             | Gennemsnit af `days_rented` pr. gæst                         | Reservation / Guest |
| **Gæster i alt**                   | Antal unikke gæster i gæstedatabasen                         | Guest               |
| **Omsætning pr. sæson**            | Summeret `price` pr. sæson (High/Mid/Low)                    | Room                |
| **Omsætning pr. land**             | Summeret `price` pr. `country`                               | Guest               |
| **Mest indbringende værelsestype** | Værelsestype med højeste summerede `price`                   | Room                |
| **Mest værdifulde marked**         | Land med højeste omsætning                                   | Guest               |

### Datakonsistens

For at sikre sammenlignelige resultater mellem Streamlit, Flask-services og Tableau:

* Revenue beregnes **direkte ud fra kolonnen `Price`**
* NaN- og tomme landefelter fjernes under indlæsning
* Alle tal konverteres til numeriske værdier med `pd.to_numeric(..., errors="coerce")`
* Landenavne ensartes med `str.title()`

Dette sikrer, at totaler, top-lande og sæsondata stemmer 1:1 med Tableau-udregningerne.

---

## 8. API-gateway og endpoints

API-gatewayen fungerer som et centralt bindeled mellem frontend og alle microservices.
Den håndterer routing, fejlhåndtering og sikrer, at Streamlit kan hente data via én konsistent base-URL.

### Struktur

* Base-URL: `http://localhost:8000/api/`
* Eksempel: `http://localhost:8000/api/guest/guests/summary`

### Samlede endpoints (uddrag)

| Service         | Endpoint                                | Metode | Beskrivelse                                           |
| --------------- | --------------------------------------- | ------ | ----------------------------------------------------- |
| **Room**        | `/rooms`                                | GET    | Returnerer alle værelser (CSV → SQLite)               |
|                 | `/rooms/revenue/by_country`             | GET    | Omsætning pr. land                                    |
|                 | `/rooms/revenue/by_roomtype_and_season` | GET    | Omsætning pr. sæson og værelsestype                   |
|                 | `/rooms/revenue/total`                  | GET    | Samlet værelsesomsætning                              |
| **Guest**       | `/guests`                               | GET    | Alle gæster                                           |
|                 | `/guests/summary`                       | GET    | Samlet gæsteanalyse (lande, sæson, roomtype-heatmap)  |
| **Reservation** | `/reservations`                         | GET    | Alle reservationer                                    |
|                 | `/reservations/summary`                 | GET    | KPI’er for reservationer (ADR, gennemsnit, omsætning) |
| **Bar**         | `/bar/summary`                          | GET    | Omsætning, gennemsnitspris og top-produkter           |
|                 | `/bar/search?q=`                        | GET    | Søg i barens produkter                                |
| **Analytics**   | `/analytics/overview`                   | GET    | Samlet KPI-oversigt (samler alle services)            |
|                 | `/analytics/monthly_revenue`            | GET    | Månedlig omsætning                                    |
| **Gateway**     | `/api/health`                           | GET    | Status for alle services                              |

### De vigtigste endpoints

Frontendens to dashboards henter primært data fra følgende:

* **Overview:** `/api/analytics/overview` + `/api/analytics/monthly_revenue`
* **Guest & Country:** `/api/guest/guests/summary`

Alle andre endpoints er tilgængelige for dybere analyser eller videreudvikling (fx særskilte sider for bar-data eller reservationer).

---

## 9. Docker-opsætning

Projektet benytter Docker Compose til at bygge og orkestrere alle services.
Hver service defineres med eget image, port og volume-mount.

### Eksempel (forkortet)

```yaml
version: "3.9"

services:
  room:
    build: ./services/room
    container_name: room_service
    volumes:
      - ./data:/app/data
    ports:
      - "5001:5001"

  guest:
    build: ./services/guest
    container_name: guest_service
    volumes:
      - ./data:/app/data
    ports:
      - "5003:5003"

  analytics:
    build: ./services/analytics
    container_name: analytics_service
    ports:
      - "5005:5005"
    depends_on:
      - room
      - guest
      - reservation
      - bar

  gateway:
    build: ./api-gateway
    container_name: api_gateway
    ports:
      - "8000:8000"
    depends_on:
      - room
      - bar
      - guest
      - reservation
      - analytics

  frontend:
    build: ./frontend-streamlit
    container_name: frontend_streamlit
    ports:
      - "8501:8501"
    depends_on:
      - gateway
```

### Netværk og volumes

* Alle services er tilknyttet netværket **`hotel_arthur_net`**.
* Fælles data deles via `./data:/app/data`.
* Hver service bruger egen port og SQLite-database.

Docker-miljøet muliggør, at projektet kan køres identisk på enhver maskine uden ekstra opsætning.

---

Her kommer **Del 4 (README – punkterne 11, 12 og 14)**, som afrunder hele dokumentationen i samme konsistente markdown-stil:

---

## 11. Frontend (Streamlit)

Frontend-delen er udviklet i **Streamlit** og fungerer som den visuelle præsentation af data fra de bagvedliggende microservices.
Dashboardet er opdelt i flere sider, som henter data gennem API Gateway’en.

### Oversigt over sider

| Side                | Formål                                                                                          | Primære datakilder                                          |
| ------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **Overview**        | Viser hotellets samlede performance: total omsætning, ADR, opholdslængde og månedlig udvikling. | `/api/analytics/overview`, `/api/analytics/monthly_revenue` |
| **Guest & Country** | Viser fordeling af gæster, omsætning pr. land, samt sammenhæng mellem sæson og værelsestype.    | `/api/guest/guests/summary`                                 |
| **Room Insights**   | Visualiserer de mest indbringende værelser og deres fordeling over måneder og sæsoner.          | `/api/room/rooms/revenue/...`                               |
| **Bar Dashboard**   | Viser barens omsætning og salg fordelt på produktkategori, inkl. søgefunktion.                  | `/api/bar/summary`, `/api/bar/search`                       |

### Nøglefunktioner

* **Automatisk dataopdatering:** alle fetches går gennem `API_BASE` (gateway), med caching (TTL=60 sekunder).
* **Dansk formatering:** tal vises i DKK-format med punktum som tusindtalsseparator og komma som decimalseparator.
* **Altair-visualiseringer:** anvendes til interaktive grafer og heatmaps.
* **Robust fallback:** ved netværksfejl anvendes mock-data, så dashboardet stadig kan vises.
* **Responsivt layout:** `layout="wide"` giver plads til KPI’er og grafer side om side.

---

## 12. Health checks og debugging

Alle services indeholder endpoints til at overvåge systemets tilstand.
Dette sikrer, at problemer kan spores hurtigt, både under udvikling og ved drift.

### Health-check endpoints

| Service         | Endpoint            | Returnerer                                  |
| --------------- | ------------------- | ------------------------------------------- |
| **Room**        | `/health`           | Status for database og tabeller             |
| **Guest**       | `/health`           | Status for gæstetabel og afhængigheder      |
| **Reservation** | `/health`           | Status for reservationer og SQLite          |
| **Bar**         | `/health`           | Status for barens datakilde                 |
| **Analytics**   | `/analytics/health` | Samlet status for afhængige services        |
| **Gateway**     | `/api/health`       | Overblik over hele systemets tilgængelighed |

### Typiske fejlkilder og løsninger

| Problem                                           | Årsag                                   | Løsning                                               |
| ------------------------------------------------- | --------------------------------------- | ----------------------------------------------------- |
| 504 Gateway Timeout                               | En service ikke tilgængelig i netværket | Kontrollér at containeren kører (`docker ps`)         |
| “ModuleNotFoundError: No module named 'requests'” | Manglende dependency i requirements.txt | Tilføj `requests` og rebuild containeren              |
| “No such file or directory: room.db”              | Database ikke oprettet                  | Kontrollér at `/data`-mappen er delt korrekt          |
| “LIMIT” på data i output                          | Begrænsning i SQL-query                 | Fjern `LIMIT` i `app.py` for at returnere alle rækker |

**Debug-tips:**

* `docker-compose logs <servicenavn>` – se realtidslogs
* `curl http://localhost:8000/api/health` – samlet systemstatus
* `st.cache_data.clear()` i Streamlit – ryd cache ved test af live-opdateringer

---

## 14. Udvidelsesmuligheder

Projektet er designet med en modulær arkitektur, så nye komponenter nemt kan tilføjes.
Nedenfor er forslag til realistiske og teknisk relevante udvidelser.

### Funktionelle udvidelser

* **Brugerlogin og adgangsniveauer:** så medarbejdere kan se specifikke dashboards (f.eks. bar-personale vs. ledelse).
* **Upload af nye CSV’er via UI:** Streamlit kunne tillade upload, hvorefter services regenererer databaser automatisk.
* **Automatiske e-mailrapporter:** daglige/ugentlige KPI’er sendt fra analytics_service.
* **Flere dashboards:** fx “Reservation Trends” eller “Revenue Forecast”.

### Tekniske forbedringer

* **CI/CD-integration:** GitHub Actions til automatisk test og build ved push.
* **Test-suite:** Pytest til unit-tests af API’er og datafunktioner.
* **Caching på gateway-niveau:** reducerer svartid ved gentagne kald.
* **Central logging:** opsamling af logdata fra alle services i ét overvågningsdashboard.
* **Graf-database:** mulighed for at udvide dataanalyse ved at forbinde relationer mellem gæster, lande og bookingtyper.

### Skalering og drift

* Flytning til **Docker Swarm eller Kubernetes** for container-orchestration.
* Integrering med **eksterne datakilder** (CRM, bookingsystemer, online reviews).
* Opsætning af **load balancer** foran API Gateway ved højt trafikniveau.

---

**Afsluttende bemærkning:**
Systemet for Hotel Kong Arthur viser, hvordan et distribueret Python-baseret setup kan levere pålidelige, opdaterede og gennemsigtige nøgletal til virksomhedsdrift.
Kombinationen af Flask-microservices, API Gateway, SQLite og Streamlit udgør en fuld datakæde fra kilde til indsigt — let at forstå, udbygge og anvende i praksis.

---

Designet, testet og bygget af The Rizzlers, ifm Hotel Kong Arthur mini projektet, 3. semester, EK-ITA24
