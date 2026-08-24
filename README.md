# Gridiron Manager

Böngészős amerikaifutball-menedzser játék. A felhasználó egy valódi NFL-csapatot választ, megkapja annak aktuális rosterét, edzi és fejleszti a játékosokat, kiválasztja a kezdőcsapatát, szponzori szerződéseket köt, fejleszti a stadiont, és a liga többi csapatával — más felhasználókkal **és AI-vezérelt bot-franchise-okkal** — versenyez, kereskedik és tárgyal egy divíziókra bontott, 32 csapatos ligában.

A részletes eredeti koncepciót lásd: [terv.md](terv.md).

## Tech stack

- **Backend**: Python / FastAPI, SQLAlchemy 2.0, Alembic (migrációk), PostgreSQL, APScheduler (napi ütemezés)
- **Frontend**: React + TypeScript, Vite, Tailwind CSS, Framer Motion
- **Infrastruktúra**: Docker Compose (`db`, `backend`, `frontend` konténerek)
- **Adatforrás**: ESPN nyilvános (nem hivatalos) API — valódi NFL-játékosnevek, korok és fejléc-fotó URL-ek

## Indítás

```bash
docker compose up -d
```

- Backend: http://localhost:8000 (Swagger UI: `/docs`)
- Frontend: http://localhost:5173
- PostgreSQL: `localhost:5432` (user/pass/db: `gridiron`)

Első indításkor a backend automatikusan lefuttatja az Alembic migrációkat (`alembic upgrade head`), feltölt egy kis tartalék szabadügynök-poolt, ha üres a `players` tábla, **és minden még gazdátlan NFL-csapatot AI-bottal tölt fel**, hogy a liga induláskor is teljes és játszható legyen.

### Adatbázis migráció kézzel

```bash
docker compose exec backend alembic revision --autogenerate -m "leírás"
docker compose exec backend alembic upgrade head
```

## Projekt felépítés

```
backend/
  app/
    core/        üzleti logika (gazdaság, szimuláció, edzés, piac, csere, ütemezés, botok...)
    models/       SQLAlchemy modellek
    schemas/      Pydantic sémák (API be/kimenet)
    routers/      FastAPI végpontok
    scripts/      egyszeri/dev célú szkriptek (import, bot-seedelés, reset)
    main.py       FastAPI app, router-regisztráció, induláskori feladatok
  alembic/        adatbázis-migrációk
frontend/
  src/
    api/client.ts    a teljes backend API TypeScript kliense
    pages/           oldalak (Login, Register, SelectTeam, Dashboard)
    pages/dashboard/ a Dashboard fülei (Áttekintés, Liga, Keret, Piac, Tárgyalások, Meccsek)
    components/      újrahasznosítható UI elemek (PlayerCard, MatchViewer, Skeleton...)
    playerTier.ts    OVR-alapú kártya-szintezés (arany/ezüst/bronz/sima)
docker-compose.yml
```

## Játékmenet

### 1. Regisztráció és csapatválasztás

A regisztráció (`POST /auth/register`) csak e-mailt, jelszót és menedzsernevet kér — **nincs csapatválasztás ekkor**. Bejelentkezés után, ha a felhasználónak még nincs csapata, a `/select-team` oldalra kerül: liga választás (`GET /league/available`), majd az adott liga egyik csapata (`POST /teams/claim`, `league_key` + `nfl_team_code`).

Két liga érhető el, teljesen független csapatokkal, ligatáblákkal, szezonokkal és szabadügynök-poollal (`app/core/game_data.py: LEAGUES`):
- **NFL** (`nfl`) — a valódi 32 csapat, 8 divízió.
- **College Football** (`college`) — egy kézzel válogatott, valós ESPN-rosterrel rendelkező 32 csapatos kör (a CFL és egy európai liga rosteradatai nem elérhetők az ESPN API-n, ezért csak az NCAA valósult meg második ligaként), ugyanolyan 8 divíziós/playoff-szerkezettel, `CF-` előtagú csapatkódokkal.

- Ha a csapatot még senki (ember) nem választotta, de **AI bot vezeti**, a "kiválasztás" átveszi tőle a már működő, teljes rosterrel és eddigi állással rendelkező franchise-t (a bot-fiók törlődik).
- Ha egy másik ember már lefoglalta, a választás elutasítva.
- A csapat kezdéskor **csak a 3 legjobb overallú játékost kapja meg pozíciónként** (nem a teljes ~70-90 fős valódi rostert) — a többi a szabadügynök-piacon marad, onnan igazolható. Ez érvényes akkor is, ha egy már bot-irányított, feltöltött csapatot vesz át valaki.
- Bármikor lecserélhető a csapat (`POST /teams/release`): a jelenlegi csapatot azonnal átveszi egy AI, a felhasználó pedig újra a `/select-team`-re kerül, bármelyik ligában választhat újat. A korábbi csapat szezon-történeti eredményei megmaradnak, a tulajdonostól függetlenül.

### 2. Liga: divíziók, állás, sorsolás

A liga a valódi NFL 8 divíziójára épül (AFC/NFC × East/North/South/West, `app/core/game_data.py: NFL_DIVISIONS`). A **Liga fülön** (`GET /league/standings`, `GET /league/schedule`) látható:

- **Állás**: minden divízió csapatai győzelem/vereség/döntetlen szerint rendezve
- **Sorsolás**: a liga összes előre kiírt, még le nem játszott meccse, dátummal — a saját meccs kiemelve

A meccsek **egy nappal előre generálódnak**, nem csak a lejátszás pillanatában dőlnek el (`app/core/league_schedule.py`). Minden csapat első meccse a csatlakozást követő nap 21:00-kor van (Europe/Budapest idő); utána, amint egy csapat lejátssza a meccsét, automatikusan sorsolást kap a következő napra. Egy APScheduler job minden nap 21:00-kor lefuttatja a teljes napi ciklust (`app/core/daily_cycle.py`):

1. lejátssza az aznapra kiírt, esedékes meccseket, és frissíti a Gy-V-D állást
2. jóváírja a stadionbevételt (±10% RNG) és a szponzori kifizetéseket minden csapatnak
3. feltölti a szabadügynök-piacot, ha a pool 15 alá csökkent
4. **sorsolja a következő fordulót** minden csapatnak, akinek nincs még függő meccse
5. elbírálja a bot-csapatoknak küldött függőben lévő csereajánlatokat

Manuális/teszt trigger: `POST /matches/run-daily-cycle`. A saját következő meccs és ellenfél az Áttekintés fülön (`GET /matches/upcoming`) is látszik.

### 3. Szezon és rájátszás

A liga valódi szezonokban játszik (`app/core/season_manager.py`, `GET /league/season`):

- **Alapszakasz**: 17 nap (`REGULAR_SEASON_DAYS`). Minden nap a napi ciklus lejátssza az esedékes meccseket és frissíti a Gy-V-D állást.
- **Rájátszás**: a 17. nap után minden divízió győztese (8 csapat, 4/konferencia) bekerül egy egyenes kieséses ágrajzba: konferencia-elődöntő → konferencia-döntő → **Super Bowl**. A résztvevők, konferenciabajnokok és a Super Bowl-győztes egyszeri pénzjutalmat kapnak (rendre 200 000 / 500 000 / 2 000 000 FT).
- **Szezonváltás**: a Super Bowl után minden csapat Gy-V-D-je nullázódik, minden játékos 1 évet öregszik, majd a nyugdíjkorhatárt (RB: 33, minden más pozíció: 36 év) elérők visszavonulnak — helyükre azonos számú, 20-22 éves, alacsony OVR-ű "rookie" kerül a szabadügynök-piacra. Ezután azonnal indul a következő szezon alapszakasza.

A Liga fülön mindig látszik az aktuális szezon, fázis és nap/forduló.

### 4. Kezdőcsapat kiválasztása

A Keret fülön kiválasztható, ki induljon a következő meccsen: 1 QB, 2 RB, 2 WR, 1 TE, 1 DEF (`PUT /roster/lineup`, `app/core/roster.py: set_starting_lineup`). Amit nem állítasz be, azt a szimulációs motor automatikusan a legjobb OVR-ű, adott pozíciós játékossal tölti fel — tehát sosem törik el, ha valaki soha nem nyúl a felálláshoz (pl. a bot-csapatok).

### 5. Edzés (játékosfejlesztés)

3 egyidejű edzésslot csapatonként, 18 órás edzésidő. XP-t ad, kor-szorzóval (18-21 év: 1.5x, 22-25: 1.0x, 26-29: 0.5x, 30+: 0.1x). `POST /training/start`, `POST /training/{id}/collect`.

### 6. Stadion

4 szint, mindegyik növekvő kapacitással, bevétellel és **építési idővel** (12h / 24h / 48h a 2./3./4. szintre). `POST /stadium/upgrade/start` majd `POST /stadium/upgrade/collect`, amint elkészült.

### 7. Szponzorok

5 különböző sablon (`GET /sponsors/templates`), 3-7 napos időtartammal (max 3 aktív egyszerre):

| Sablon | Napi bevétel | Győzelmi bónusz | Időtartam |
|---|---|---|---|
| Megbízható Partner | 25 000 FT | – | 7 nap |
| Teljesítmény Szponzor | 8 000 FT | 50 000 FT | 7 nap |
| Kockázatvállaló Befektető | 3 000 FT | 90 000 FT | 5 nap |
| Villám Kampány | 45 000 FT | – | 3 nap |
| Helyi Vállalkozás | 15 000 FT | 20 000 FT | 7 nap |

### 8. Piac és transzferek

- **Szabadügynökök** (`GET /market/`): valódi NFL-játékosok, akiknek a csapatát még senki nem választotta. Szűrhető pozíció és név szerint, lapozva (`limit`/`offset`, a válasz `X-Total-Count` fejlécében a teljes találatszámmal — a Piac fülön "Előző/Következő oldal" gombokkal).
- **Elengedés** (`POST /roster/{id}/release`): saját játékos visszakerül szabadügynöknek.
- **Transzferlista** (`POST /roster/{id}/list-for-transfer`): saját játékos eladásra kínálása egy általad megadott áron, más felhasználók megvehetik (`POST /transfers/{id}/buy`) — a bevétel közvetlenül hozzád kerül.
- **Tárgyalások** (`/trades/*`): ajánlatot tehetsz bármelyik másik csapat (ember vagy bot) bármelyik játékosáért, böngészve a rosterüket (`GET /teams/{id}/roster`); készpénz és/vagy saját játékos cserébe. A célcsapat elfogadhatja/elutasíthatja; elfogadáskor minden más függőben lévő, ugyanazt a játékost érintő ajánlat automatikusan visszavonódik.

### 9. Meccsszimuláció

`app/core/simulation.py`: a kiválasztott (vagy automatikusan feltöltött) kezdőcsapat ereje és a taktikai szorzók (Pass-heavy, Run-heavy, Blitz, Prevent) alapján súlyozott véletlen eredményt és emberi olvasható meccsnaplót generál. `POST /matches/practice` egy azonnali gyakorlómeccshez generált AI-ellenféllel (nem befolyásolja a gazdaságot, nem kerül a liga-történetbe).

## AI bot-csapatok

Minden NFL-csapat, amit még nem választott ember, **AI-vezérelt bot** irányítja (`app/core/bots.py`), hogy mindig legyen teljes, 32 csapatos, játszható liga:

- A botok ugyanazzal a szimulációs motorral és napi ciklussal játszanak, mint az emberek — nincs külön, nehézsúlyú AI-logika, a botok egyszerűen csapatként léteznek a rendszerben.
- **Nem edzenek, nem fejlesztenek stadiont, nem kötnek szponzori szerződést** — direkt egyszerűen tartva, hogy a szimuláció könnyű maradjon.
- **"Gumiszalag" fejlődés**: mivel a botok nem edzenek, a napi ciklus 7 naponta +1 OVR-t ad a teljes bot-rosternek (99-es sapkával), hogy a liga ne stagnáljon az edző emberi csapatokhoz képest. Ez egyetlen tömeges DB-frissítés, nincs mögötte semmilyen döntéshozatal.
- **Csereajánlatokat viszont elbírálnak**: a napi ciklus során minden nekik küldött függő ajánlatot egy egyszerű szabály dönt el — elfogadják, ha a felajánlott érték (készpénz + felajánlott játékos piaci ára) eléri a kért játékos értékének legalább 90%-át, egyébként elutasítják.
- Bármelyik bot-csapatot **átveheted** a csapatválasztón keresztül — ilyenkor a roster és az addigi állás megmarad, csak gazdát cserél.

## Vizuális dizájn

- **Sportkártya-dizájn** (`components/PlayerCard.tsx`, `playerTier.ts`): a játékosok OVR alapján arany (90+, csillogó animációval), ezüst (80-89), bronz (70-79) vagy sima sötét (70 alatt) kártyaként jelennek meg a piacon, a transzferlistán és a saját keretben.
- **Sötét, "öltözői" téma**: smaragdzöld (`emerald-400`) akcens ciánkék másodlagos jelzésekkel (pl. "AI vezényli" felirat), Tailwind-tokenként (`tailwind.config.js: gridiron.accent/cyan`).
- **Animált meccsnéző** (`components/MatchViewer.tsx`): élő pontszám-számláló, negyedjelző, soronként megjelenő játéknapló, és berobbanó "TOUCHDOWN!" felirat izzó effekttel. Használva a gyakorlómeccsnél és a liga-meccsek visszajátszásánál (Meccsek fül, egy lejátszott meccsre kattintva).
- **Skeleton loaderek** (`components/Skeleton.tsx`): pulzáló kártya-sziluettek "Betöltés..." szöveg helyett minden fülön és a kezdeti csapat-betöltésnél.

## Admin / teszt óra (csak fejlesztéshez)

Az Admin fülön (`app/core/clock.py`, `/admin/*` végpontok) egy megosztott, egész ligára érvényes virtuális óra léptethető előre (+1/+6/+12/+24 óra gombokkal), hogy edzés, stadionfejlesztés és meccsek végigjátszásához ne kelljen valós időt várni:

- Az edzés, a stadionfejlesztés, a szponzor-lejárat és a napi ciklus esedékesség-vizsgálata mind ezt a virtuális órát nézi (`now_utc(db)`), nem a valós rendszeridőt.
- Az "idő előreléptetése" gomb rögtön le is futtatja a napi ciklust, így az időközben esedékessé vált meccsek is azonnal lejátszódnak.
- A frontend (`context/TimeContext.tsx`) is ismeri ezt az eltolást, így a visszaszámlálók és a "kész" gombok a szimulált időhöz igazodnak, nem a böngésző valós órájához.
- A szezon/rájátszás dátum-logikája (mikor kap valaki új sorsolást) továbbra is a valós idő alapján fut — ez a virtuális óra kifejezetten az edzés/stadion/meccs-esedékesség gyors teszteléséhez készült.

## Valódi NFL-adatok

Az importált játékosnevek, korok és fejléc-fotó URL-ek forrása az ESPN nyilvános, de **nem hivatalosan licencelt** site API-ja. A backend csak a fotó URL-jét tárolja — a képfájlokat nem tölti le/hosztolja újra, a frontend közvetlenül az ESPN CDN-jéről tölti be őket. Ez a projekt **kizárólag személyes, nem kereskedelmi célra** használja ezt az adatot; nyilvános közzététel/kereskedelmi használat esetén NFL/NFLPA licenc kellene hozzá.

Az OVR-értékelés **nincs** a forrásadatban — azt a játék generálja (`app/scripts/import_nfl_players.py: generate_overall`), enyhén a valós NFL-tapasztalat (szezonok száma) alapján súlyozva, de nem valódi képességmérés.

## Dev szkriptek

Mindegyik a backend konténeren belül futtatandó:

```bash
# Feltölti/frissíti az adatbázist az összes NFL csapat aktuális rosterével (~2300+ játékos)
docker compose exec backend python -m app.scripts.import_nfl_players

# Ugyanez a college football liga 32 kiválasztott csapatához (~2500+ játékos)
docker compose exec backend python -m app.scripts.import_college_players

# Minden gazdátlan csapatot (mindkét ligában) AI-bottal tölt fel (indításkor automatikusan
# lefut, ez a manuális újra-seedeléshez kell, pl. reset után ha a backend nem indult újra)
docker compose exec backend python -m app.scripts.seed_bot_teams

# Töröl minden felhasználót, csapatot és a hozzájuk tartozó adatot (edzés, szponzor,
# stadion-fejlesztés, meccs, csereajánlat), majd újra feltölti a ligát AI-botokkal.
# A valódi importált játékosok megmaradnak, csak visszakerülnek a szabadügynök-piacra.
# Tiszta lappal induláshoz.
docker compose exec backend python -m app.scripts.reset_test_data
```

## Környezeti változók (backend)

Lásd [backend/app/core/config.py](backend/app/core/config.py). A docker-compose.yml-ben beállítva: `DATABASE_URL`, `JWT_SECRET_KEY`. Éles/megosztott környezetben mindenképp cseréld le a `JWT_SECRET_KEY` alapértékét.

## Kitelepítés

Éles szerverre telepítéshez lásd [DEPLOY.md](DEPLOY.md) — `main`-re pusholva a GitHub Actions build-eli és publikálja a Docker image-eket (GHCR), majd SSH-n automatikusan frissíti a szerveren futó konténereket.

## Ismert korlátok / lehetséges következő lépések

- Az alapszakasz sorsolása egyszerű, véletlenszerű napi párosítás (nem valódi NFL-szerű, divízión belüli/kívüli eltérő gyakoriságú menetrend), a rájátszás viszont valódi, ágrajz-alapú kiesés.
- A gyakorlómeccs (`/matches/practice`) nem hat a gazdaságra és nem kerül a liga-történetbe, csak a motor kipróbálására való.
- A bot-csapatok soha nem edzenek, nem fejlesztik a stadiont, és nem kötnek szponzori szerződést — helyette egy heti sima OVR-bónusszal maradnak versenyképesek, és csereajánlatokat bírálnak el.
- Mobilra portolás (React Native / PWA) még nem történt meg — a backend REST API-alapú, JWT-s auth-hal, így ez később zökkenőmentesen megoldható (lásd [terv.md](terv.md) 6. fejezet).
- Nincs admin felület a liga/szponzor-sablonok stb. szerkesztésére; ezek a kódban (`app/core/game_data.py`) vannak konfigurálva.
- A `/teams/{id}/roster` és a saját `/teams/me` végpont még mindig a teljes rostert küldi (ott ez szükséges is), csak a lista-/állás-nézetek (`/teams/`, `/league/standings`) könnyítettek Ø OVR-re.
- Az admin virtuális óra **egyetlen, az egész ligára közös** eltolás (nincs csapatonkénti időutazás) — bármelyik felhasználó léptetése mindenki edzését/meccsét/stadionját érinti, úgyhogy ne fusson egyszerre több ember tesztelése ugyanazon a példányon, ha nem akarják egymás óráját ugráltatni.
