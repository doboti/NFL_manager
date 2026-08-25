# Gridiron Manager

Böngészős amerikaifutball-menedzser játék. A felhasználó egy valódi NFL- (vagy college football-) csapatot választ, megkapja annak aktuális rosterét, edzi és fejleszti a játékosokat, kiválasztja a kezdőcsapatát, szponzori szerződéseket köt, fejleszti a stadiont, és a liga többi csapatával — más felhasználókkal **és AI-vezérelt bot-franchise-okkal** — versenyez, kereskedik és tárgyal egy divíziókra bontott, 32 csapatos ligában.

A részletes eredeti koncepciót lásd: [terv.md](terv.md).

## Tech stack

- **Backend**: Python / FastAPI, SQLAlchemy 2.0, Alembic (migrációk), PostgreSQL, APScheduler (napi ütemezés)
- **Frontend**: React + TypeScript, Vite, Tailwind CSS, Framer Motion, lucide-react (ikonok)
- **Infrastruktúra**: Docker Compose (`db`, `backend`, `frontend` konténerek)
- **Adatforrás**: ESPN nyilvános (nem hivatalos) API — valódi játékosnevek, korok és fejléc-fotó URL-ek

## Indítás

```bash
docker compose up -d
```

- Backend: http://localhost:8000 (Swagger UI: `/docs`)
- Frontend: http://localhost:5173
- PostgreSQL: `localhost:5432` (user/pass/db: `gridiron`)

Első indításkor a backend automatikusan lefuttatja az Alembic migrációkat (`alembic upgrade head`), feltölt egy kis tartalék szabadügynök-poolt, ha üres a `players` tábla, **és minden még gazdátlan csapatot AI-bottal tölt fel** (mindkét ligában), hogy a liga induláskor is teljes és játszható legyen.

### Adatbázis migráció kézzel

```bash
docker compose exec backend alembic revision --autogenerate -m "leírás"
docker compose exec backend alembic upgrade head
```

## Projekt felépítés

```
backend/
  app/
    core/        üzleti logika (gazdaság, szimuláció, edzés, piac, csere, ütemezés, botok, sérülések, progresszió...)
    models/       SQLAlchemy modellek
    schemas/      Pydantic sémák (API be/kimenet)
    routers/      FastAPI végpontok
    scripts/      egyszeri/dev célú szkriptek (import, bot-seedelés, reset)
    main.py       FastAPI app, router-regisztráció, induláskori feladatok
  alembic/        adatbázis-migrációk
frontend/
  src/
    api/client.ts    a teljes backend API TypeScript kliense
    pages/           oldalak (Login, Register, Profile, SelectTeam, Dashboard, Admin)
    pages/dashboard/ a Dashboard fülei (Áttekintés, Liga, Keret, Piac, Tárgyalások, Meccsek)
    components/      újrahasznosítható UI elemek (Sidebar, PlayerCard, MatchViewer, ui.tsx, Skeleton...)
    context/         React contextek (Auth, virtuális idő, csapatszín-téma)
    teamTheme.ts      csapatszín → CSS-változó/kontraszt segédfüggvények
    playerTier.ts    OVR-alapú kártya-szintezés (arany/ezüst/bronz/sima)
docker-compose.yml
```

## Játékmenet

### 1. Regisztráció, profil és csapatválasztás

A regisztráció (`POST /auth/register`) csak e-mailt, jelszót és menedzsernevet kér — **nincs csapatválasztás ekkor**. Regisztráció (és minden olyan bejelentkezés, ahol épp nincs csapatod) után a **Profil oldal** (`/profile`, `GET /auth/profile`) az alapértelmezett landolás: itt látszik a menedzser szintje, a trófeák/achievementek, jelszó módosítható, és innen indul a liga/csapatválasztás. Csak ha már van csapatod, kerülsz egyenesen a Dashboardra.

A csapatválasztás (`/select-team`) két lépéses: liga választás (`GET /league/available`), majd az adott liga egyik csapata (`POST /teams/claim`, `league_key` + `nfl_team_code`) — valódi csapatlogóval minden választható csapaton.

Két liga érhető el, teljesen független csapatokkal, ligatáblákkal, szezonokkal és szabadügynök-poollal (`app/core/game_data.py: LEAGUES`):
- **NFL** (`nfl`) — a valódi 32 csapat, 8 divízió.
- **College Football** (`college`) — egy kézzel válogatott, valós ESPN-rosterrel rendelkező 32 csapatos kör (a CFL és egy európai liga rosteradatai nem elérhetők az ESPN API-n, ezért csak az NCAA valósult meg második ligaként), ugyanolyan 8 divíziós/playoff-szerkezettel, `CF-` előtagú csapatkódokkal.

- Ha a csapatot még senki (ember) nem választotta, de **AI bot vezeti**, a "kiválasztás" átveszi tőle a már működő, teljes rosterrel és eddigi állással rendelkező franchise-t (a bot-fiók törlődik).
- Ha egy másik ember már lefoglalta, a választás elutasítva.
- A csapat kezdéskor **csak a 3 legjobb overallú játékost kapja meg pozíciónként** (nem a teljes ~70-90 fős valódi rostert) — a többi a szabadügynök-piacon marad, onnan igazolható. Ez érvényes akkor is, ha egy már bot-irányított, feltöltött csapatot vesz át valaki.
- Bármikor lecserélhető a csapat (`POST /teams/release`): a jelenlegi csapatot azonnal átveszi egy AI, a felhasználó pedig újra a `/select-team`-re kerül, bármelyik ligában választhat újat. A korábbi csapat szezon-történeti eredményei megmaradnak, a tulajdonostól függetlenül.
- Egy felhasználó jelenleg **egyszerre csak egyetlen csapatot** birtokolhat, bármelyik ligában (a Profil oldalon látható "liga-slot" rendszer az egyszerre több liga/csapat egyidejű menedzselésének előkészítése egy jövőbeli fázisban — ma a szint csak azt szabja meg, mikor jelenik meg a 2./3. slot mint koncepció, funkcionálisan még nincs kihasználva).

### 2. Menedzser profil, szint és achievementek

A menedzser **személyhez, nem csapathoz** kötött karrier-adatai (`app/core/progression.py`, `app/core/achievements.py`, `GET /auth/profile`):

- **Szint**: `1 + lejátszott szezonok száma` — minden lezárt szezon (sajátodként vagy egy korábbi csapatoddal) beleszámít, csapatváltástól függetlenül.
- **Trófeák/achievementek**: 11 db, a `SeasonHistory` rekordokból számolva on-the-fly (első szezon, rájátszás, konferenciabajnok, bajnok, dinasztia, veretlen szezon, összesített győzelmek, veterán menedzser stb.) — nincs külön "megszerzett" tábla, mindig a tényleges szezon-történetből derül ki.
- **Jelszó módosítás**: `PUT /auth/password`, jelenlegi jelszó ellenőrzésével.

### 3. Liga: divíziók, állás, sorsolás, rájátszás-ágrajz

A liga a valódi NFL 8 divíziójára épül (AFC/NFC × East/North/South/West, `app/core/game_data.py: NFL_DIVISIONS`, a college liga hasonló szerkezetű saját konferenciákkal). A **Liga fülön** látható:

- **Állás** (`GET /league/standings`): minden divízió csapatai győzelem/vereség/döntetlen szerint rendezve, Ø OVR-rel, a csapatnévre kattintva megnyitható a roster.
- **Sorsolás** (`GET /league/schedule`): a liga összes előre kiírt, még le nem játszott meccse, dátummal — a saját meccs kiemelve.
- **Rájátszás-ágrajz** (`GET /league/playoffs`): a folyó szezon összes rájátszás-meccse fordulónként (konferencia-elődöntő → konferencia-döntő → Super Bowl), eredménnyel vagy időponttal — akkor is látszik, ha a saját csapat nem jutott be, hogy a teljes mezőny alakulása követhető legyen.

A meccsek **egy nappal előre generálódnak**, nem csak a lejátszás pillanatában dőlnek el (`app/core/league_schedule.py`). Minden csapat első meccse a csatlakozást követő nap 21:00-kor van (Europe/Budapest idő); utána, amint egy csapat lejátssza a meccsét, automatikusan sorsolást kap a következő napra. Egy APScheduler job minden nap 21:00-kor lefuttatja a teljes napi ciklust (`app/core/daily_cycle.py`), minden ligára:

1. lejátssza az aznapra kiírt, esedékes meccseket, frissíti a Gy-V-D állást, és (kis eséllyel) sérülést oszt a pályára lépő játékosok közül
2. jóváírja a stadionbevételt (±10% RNG) és a szponzori kifizetéseket minden csapatnak
3. feltölti a szabadügynök-piacot, ha a pool 15 alá csökkent
4. **sorsolja a következő fordulót** minden csapatnak, akinek nincs még függő meccse
5. elbírálja a bot-csapatoknak küldött függőben lévő csereajánlatokat

Manuális/teszt trigger: `POST /matches/run-daily-cycle`. A saját következő meccs és ellenfél az Áttekintés fülön (`GET /matches/upcoming`) is látszik.

### 4. Szezon, rájátszás és szezonváltás

A liga valódi szezonokban játszik (`app/core/season_manager.py`, `GET /league/season`):

- **Alapszakasz**: 17 nap (`REGULAR_SEASON_DAYS`) — egy virtuális nap egy fordulónak felel meg, ahogy a valódi NFL 17 hetes szezonja.
- **Rájátszás**: a 17. nap után minden divízió győztese (8 csapat, 4/konferencia) bekerül egy egyenes kieséses ágrajzba: konferencia-elődöntő → konferencia-döntő → **Super Bowl**. A résztvevők, konferenciabajnokok és a Super Bowl-győztes egyszeri pénzjutalmat kapnak (rendre 200 000 / 500 000 / 2 000 000 FT).
- **Szezonváltás** (Super Bowl után, mindenre kiterjed, csapatonként, bot és ember egyaránt):
  - minden csapat Gy-V-D-je nullázódik;
  - minden játékos 1 évet öregszik, OVR-je visszaáll az eredeti (import-kori) `base_overall` értékre, XP-je nullázódik — **nincs nyugdíjazás/visszavonulás**, a liga állandó rostere megmarad, csak a szezon közben edzéssel megszerzett fejlődés vész el;
  - minden csapat Franchise Tőkéje visszaáll az alap 1 000 000 FT-ra, a stadion szintje 1-re, és minden folyamatban lévő stadionfejlesztés törlődik — a gazdasági verseny minden szezonban tiszta lappal indul;
  - **minden emberi tulajdonban lévő csapat visszakerül AI-irányítás alá**, a menedzser slotja felszabadul — a következő belépéskor újra a Profil oldalon landol, és bármelyik szabad csapatot választhatja (akár ugyanazt, akár egy másik ligában). Az elért eredmények (`SeasonHistory`, ezen keresztül az achievementek/szint) a menedzser személyéhez, nem a csapathoz köthetők, így ez nem veszik el.

A Liga fülön mindig látszik az aktuális szezon, fázis és nap/forduló.

### 5. Kezdőcsapat kiválasztása

A Keret fülön kiválasztható, ki induljon a következő meccsen: 1 QB, 2 RB, 2 WR, 1 TE, 1 DEF, 1 K (`PUT /roster/lineup`, `app/core/roster.py: set_starting_lineup`). Amit nem állítasz be, azt a szimulációs motor automatikusan a legjobb OVR-ű, adott pozíciós, **épp nem edzésben lévő és nem sérült** játékossal tölti fel — tehát sosem törik el, ha valaki soha nem nyúl a felálláshoz (pl. a bot-csapatok). Edzésben lévő vagy sérült játékos explicit módon sem választható be.

### 6. Edzés (játékosfejlesztés)

3 egyidejű edzésslot csapatonként, 18 órás edzésidő. XP-t ad, kor-szorzóval (18-21 év: 1.5x, 22-25: 1.0x, 26-29: 0.5x, 30+: 0.1x). `POST /training/start`, `POST /training/{id}/collect`. Sérült játékos nem küldhető edzésbe.

### 7. Sérülések

Minden lejátszott meccs után mindkét csapat kezdő (a mérkőzésen ténylegesen szerepelt) játékosai közül kis eséllyel egy megsérülhet (`app/core/injuries.py`):

- **Gyakoriság**: ~20% esély csapatonként/meccsenként (kb. 1 sérülés/5 meccs átlagosan), de tisztán véletlen — nincs számláló vagy szabályosság, így a valóságban van, hogy sűrűbben, van, hogy ritkábban fordul elő.
- **Súlyosság**: 1-8 hét (= 1-8 kihagyott meccs, mivel egy virtuális nap egy fordulónak felel meg), erősen a rövidebb sérülések felé súlyozva — a hosszú, több hetes kiesés ritka.
- A sérült játékos a felépülésig **nem választható be a kezdőcsapatba és nem küldhető edzésbe** (a Keret fülön "Sérült" jelzéssel és visszaszámlálóval látszik), de a piacon/tárgyalásokon egyébként szabadon kezelhető marad.

### 8. Stadion

4 szint, mindegyik növekvő kapacitással, bevétellel és **építési idővel** (12h / 24h / 48h a 2./3./4. szintre). `POST /stadium/upgrade/start` majd `POST /stadium/upgrade/collect`, amint elkészült.

### 9. Szponzorok

5 különböző sablon (`GET /sponsors/templates`), 3-7 napos időtartammal (max 3 aktív egyszerre):

| Sablon | Napi bevétel | Győzelmi bónusz | Időtartam |
|---|---|---|---|
| Megbízható Partner | 25 000 FT | – | 7 nap |
| Teljesítmény Szponzor | 8 000 FT | 50 000 FT | 7 nap |
| Kockázatvállaló Befektető | 3 000 FT | 90 000 FT | 5 nap |
| Villám Kampány | 45 000 FT | – | 3 nap |
| Helyi Vállalkozás | 15 000 FT | 20 000 FT | 7 nap |

### 10. Piac és transzferek

- **Szabadügynökök** (`GET /market/`): valódi játékosok, akiknek a csapatát még senki nem választotta. Szűrhető pozíció és név szerint, lapozva (`limit`/`offset`, a válasz `X-Total-Count` fejlécében a teljes találatszámmal — a Piac fülön "Előző/Következő oldal" gombokkal).
- **Elengedés** (`POST /roster/{id}/release`): saját játékos visszakerül szabadügynöknek.
- **Transzferlista** (`POST /roster/{id}/list-for-transfer`): saját játékos eladásra kínálása egy általad megadott áron, más felhasználók megvehetik (`POST /transfers/{id}/buy`) — a bevétel közvetlenül hozzád kerül.
- **Tárgyalások** (`/trades/*`): ajánlatot tehetsz bármelyik másik csapat (ember vagy bot) bármelyik játékosáért, böngészve a rosterüket (`GET /teams/{id}/roster`); készpénz és/vagy saját játékos cserébe. A célcsapat elfogadhatja/elutasíthatja; elfogadáskor minden más függőben lévő, ugyanazt a játékost érintő ajánlat automatikusan visszavonódik.

### 11. Meccsszimuláció

`app/core/simulation.py`: a kiválasztott (vagy automatikusan feltöltött) kezdőcsapat ereje pozíciónkénti súlyozott átlag-OVR-ként (QB/WR/RB/TE/K) áll szemben az ellenfél védelmi értékelésével — mindkettő ugyanazon a ~0-99-es skálán, hogy a különbség ténylegesen eldöntse a meccset, ne csak háttérzaj legyen. A várható pontszám egy alapérték + az erőkülönbség-alapú módosító, viszonylag alacsony szórással, így egy valódi minőségi különbség megbízhatóan meglátszik az eredményen (kiegyenlített csapatoknál ~50-50% eséllyel, nagy erőkülönbségnél 90%+ eséllyel nyer az esélyesebb), de a meglepetés esélye megmarad. A taktikai szorzók (Pass-heavy, Run-heavy, Blitz, Prevent) ezt tovább módosítják. `POST /matches/practice` egy azonnali gyakorlómeccshez generált AI-ellenféllel (nem befolyásolja a gazdaságot, nem kerül a liga-történetbe, sérülést sem okozhat).

## AI bot-csapatok

Minden csapat, amit még nem választott ember, **AI-vezérelt bot** irányítja (`app/core/bots.py`), hogy mindig legyen teljes, játszható liga:

- A botok ugyanazzal a szimulációs motorral és napi ciklussal játszanak, mint az emberek — nincs külön, nehézsúlyú AI-logika, a botok egyszerűen csapatként léteznek a rendszerben.
- **Nem edzenek, nem fejlesztenek stadiont, nem kötnek szponzori szerződést** — direkt egyszerűen tartva, hogy a szimuláció könnyű maradjon.
- **"Gumiszalag" fejlődés**: mivel a botok nem edzenek, a napi ciklus 7 naponta +1 OVR-t ad a teljes bot-rosternek (99-es sapkával), hogy a liga ne stagnáljon az edző emberi csapatokhoz képest. Ez egyetlen tömeges DB-frissítés, nincs mögötte semmilyen döntéshozatal.
- **Csereajánlatokat viszont elbírálnak**: a napi ciklus során minden nekik küldött függő ajánlatot egy egyszerű szabály dönt el — elfogadják, ha a felajánlott érték (készpénz + felajánlott játékos piaci ára) eléri a kért játékos értékének legalább 90%-át, egyébként elutasítják.
- Bármelyik bot-csapatot **átveheted** a csapatválasztón keresztül — ilyenkor a roster és az addigi állás megmarad, csak gazdát cserél.

## Vizuális dizájn

- **Dashboard-váz** (`components/Sidebar.tsx`): a bejelentkezés utáni felület egy állandó bal oldali menüsávval épül fel (ikon + felirat, animált csúszó jelölő az aktív fülön), amely mobilon hamburger-menüvé/kihúzható panellé alakul.
- **Csapatszín-téma** (`teamTheme.ts`, `context/TeamThemeContext.tsx`): a Dashboard a birtokolt csapat valódi márkaszíneivel (`app/core/game_data.py: TEAM_COLORS`, mind a 64 NFL+college csapatra kézzel felvéve) tématizálódik — CSS-változóként befolyásolja a menüsáv kiemelését, a "saját csapat" jelöléseket (állás, sorsolás, rájátszás-ágrajz) és a fő gombokat. Egy kontraszt-védelem (`readableAccentHex`) gondoskodik róla, hogy egy nagyon sötét csapatszín (pl. fekete/sötétkék) is olvasható maradjon szövegként a sötét alapfelületen, miközben a tömör kitöltéseknél (gombok, aktív menüpont) a valódi márkaszín látszik.
- **Sportkártya-dizájn** (`components/PlayerCard.tsx`, `playerTier.ts`): a játékosok OVR alapján arany (90+, csillogó animációval), ezüst (80-89), bronz (70-79) vagy sima sötét (70 alatt) kártyaként jelennek meg a piacon, a transzferlistán és a saját keretben — ez a szintezés szándékosan nem csapatszínezett, hogy a játékosminőség jelzése egyértelmű maradjon.
- **Animált meccsnéző** (`components/MatchViewer.tsx`): élő pontszám-számláló, negyedjelző, soronként megjelenő játéknapló, és berobbanó "TOUCHDOWN!" felirat izzó effekttel. Használva a gyakorlómeccsnél és a liga-meccsek visszajátszásánál (Meccsek fül, egy lejátszott meccsre kattintva).
- **Skeleton loaderek** (`components/Skeleton.tsx`): pulzáló kártya-sziluettek "Betöltés..." szöveg helyett minden fülön és a kezdeti csapat-betöltésnél.

## Admin / teszt óra (csak fejlesztéshez)

Az Admin konzolon (`app/core/clock.py`, `/admin/*` végpontok, csak `is_admin` fiókoknak) egy megosztott, egész ligára érvényes virtuális óra léptethető előre (+1/+6/+12/+24 óra gombokkal), hogy edzés, stadionfejlesztés és meccsek végigjátszásához ne kelljen valós időt várni:

- Az edzés, a stadionfejlesztés, a szponzor-lejárat, a sérülés-visszaszámlálás és a napi ciklus esedékesség-vizsgálata mind ezt a virtuális órát nézi (`now_utc(db)`), nem a valós rendszeridőt.
- Az "idő előreléptetése" gomb rögtön le is futtatja a napi ciklust, így az időközben esedékessé vált meccsek is azonnal lejátszódnak.
- A frontend (`context/TimeContext.tsx`) is ismeri ezt az eltolást, így a visszaszámlálók és a "kész" gombok a szimulált időhöz igazodnak, nem a böngésző valós órájához.
- Az admin konzolon felhasználó-kezelés is elérhető (lista, törlés).

## Valódi adatok

Az importált játékosnevek, korok és fejléc-fotó URL-ek forrása az ESPN nyilvános, de **nem hivatalosan licencelt** site API-ja. A backend csak a fotó URL-jét tárolja — a képfájlokat nem tölti le/hosztolja újra, a frontend közvetlenül az ESPN CDN-jéről tölti be őket. Ez a projekt **kizárólag személyes, nem kereskedelmi célra** használja ezt az adatot; nyilvános közzététel/kereskedelmi használat esetén liga/szövetségi licenc kellene hozzá. A csapatszínek (`TEAM_COLORS`) kézzel felvitt, közismert márkaszín-párok, szintén nem hivatalos forrásból.

Az OVR-értékelés **nincs** a forrásadatban — azt a játék generálja (`app/scripts/import_nfl_players.py: generate_overall`), enyhén a valós tapasztalat (szezonok száma / college osztályév) alapján súlyozva, de nem valódi képességmérés.

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

# Javítófuttatás: rosztert ad minden olyan meglévő csapatnak (bot vagy ember), amelynek
# jelenleg 0 játékosa van -- ez akkor fordulhat elő, ha a backend első indítása (ami
# automatikusan létrehozza a bot-csapatokat) megelőzte a fenti import szkriptek lefutását.
# Csak az üres csapatokat érinti, semmit nem töröl -- élő szerveren is biztonságos.
docker compose exec backend python -m app.scripts.backfill_missing_rosters

# Töröl minden felhasználót, csapatot és a hozzájuk tartozó adatot (edzés, szponzor,
# stadion-fejlesztés, meccs, csereajánlat), majd újra feltölti a ligát AI-botokkal.
# A valódi importált játékosok megmaradnak, csak visszakerülnek a szabadügynök-piacra.
# Tiszta lappal induláshoz.
docker compose exec backend python -m app.scripts.reset_test_data
```

## Környezeti változók (backend)

Lásd [backend/app/core/config.py](backend/app/core/config.py). A docker-compose.yml-ben beállítva: `DATABASE_URL`, `JWT_SECRET_KEY`. Éles/megosztott környezetben mindenképp cseréld le a `JWT_SECRET_KEY` alapértékét.

## Kitelepítés

Éles szerverre telepítéshez lásd [DEPLOY.md](DEPLOY.md) — `main`-re pusholva a GitHub Actions build-eli és publikálja a Docker image-eket (GHCR), a tényleges éles frissítés viszont egy külön, kézzel indított workflow (`deploy-prod.yml`), hogy a szerver frissítése mindig szándékos, ellenőrzött lépés maradjon.

## Ismert korlátok / lehetséges következő lépések

- Egy felhasználó egyszerre csak egyetlen csapatot birtokolhat (bármelyik ligában) — a Profil oldal "liga-slot" kijelzése egy jövőbeli, egyszerre több liga/csapat menedzselését lehetővé tevő bővítés előkészítése, funkcionálisan még nincs kihasználva.
- Az alapszakasz sorsolása egyszerű, véletlenszerű napi párosítás (nem valódi NFL-szerű, divízión belüli/kívüli eltérő gyakoriságú menetrend), a rájátszás viszont valódi, ágrajz-alapú kiesés.
- A gyakorlómeccs (`/matches/practice`) nem hat a gazdaságra és nem kerül a liga-történetbe, csak a motor kipróbálására való.
- A bot-csapatok soha nem edzenek, nem fejlesztik a stadiont, és nem kötnek szponzori szerződést — helyette egy heti sima OVR-bónusszal maradnak versenyképesek, és csereajánlatokat bírálnak el.
- Mobilra portolás (React Native / PWA) még nem történt meg — a backend REST API-alapú, JWT-s auth-hal, így ez később zökkenőmentesen megoldható (lásd [terv.md](terv.md) 6. fejezet).
- Nincs admin felület a liga/szponzor-sablonok stb. szerkesztésére; ezek a kódban (`app/core/game_data.py`) vannak konfigurálva.
- A `/teams/{id}/roster` és a saját `/teams/me` végpont még mindig a teljes rostert küldi (ott ez szükséges is), csak a lista-/állás-nézetek (`/teams/`, `/league/standings`) könnyítettek Ø OVR-re.
- Az admin virtuális óra **egyetlen, az egész ligára közös** eltolás (nincs csapatonkénti időutazás) — bármelyik felhasználó léptetése mindenki edzését/meccsét/stadionját/sérülés-visszaszámlálóját érinti, úgyhogy ne fusson egyszerre több ember tesztelése ugyanazon a példányon, ha nem akarják egymás óráját ugráltatni.
