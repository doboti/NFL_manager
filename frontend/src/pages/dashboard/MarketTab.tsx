import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Player,
  Team,
  buyPlayer,
  buyTransferListedPlayer,
  listMarket,
  listTransferMarket,
} from "../../api/client";
import PlayerCard from "../../components/PlayerCard";
import { SkeletonCardGrid } from "../../components/Skeleton";

const MARKET_POSITIONS = ["", "QB", "RB", "WR", "TE", "K", "DEF"];
const PAGE_SIZE = 30;

interface Props {
  team: Team;
  onTeamUpdate: (team: Team) => void;
}

function PriceButton({
  price,
  priceLabel,
  disabled,
  busy,
  onBuy,
}: {
  price: number;
  priceLabel?: string;
  disabled: boolean;
  busy: boolean;
  onBuy: () => void;
}) {
  return (
    <>
      <div className="mb-1 text-center text-xs font-semibold opacity-80">
        {priceLabel ?? ""}
        {price.toLocaleString("hu-HU")} FT
      </div>
      <motion.button
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.96 }}
        disabled={disabled || busy}
        onClick={onBuy}
        className="w-full rounded-lg bg-slate-950/80 py-1.5 text-xs font-semibold text-white hover:bg-slate-950 disabled:opacity-40"
      >
        Vásárlás
      </motion.button>
    </>
  );
}

export default function MarketTab({ team, onTeamUpdate }: Props) {
  const [subTab, setSubTab] = useState<"free-agents" | "transfers">("free-agents");

  const [market, setMarket] = useState<Player[] | null>(null);
  const [marketTotal, setMarketTotal] = useState(0);
  const [marketPage, setMarketPage] = useState(0);
  const [marketPosition, setMarketPosition] = useState("");
  const [marketSearch, setMarketSearch] = useState("");

  const [transferList, setTransferList] = useState<Player[] | null>(null);

  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refreshMarket(position = marketPosition, search = marketSearch, page = marketPage) {
    const result = await listMarket({
      position: position || undefined,
      search: search || undefined,
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
    });
    setMarket(result.players);
    setMarketTotal(result.total);
  }

  useEffect(() => {
    refreshMarket().catch(() => setError("A piac betöltése nem sikerült."));
    listTransferMarket()
      .then(setTransferList)
      .catch(() => setError("A transzferpiac betöltése nem sikerült."));
  }, []);

  useEffect(() => {
    const debounce = setTimeout(() => {
      setMarketPage(0);
      refreshMarket(marketPosition, marketSearch, 0).catch(() => setError("A piac betöltése nem sikerült."));
    }, 300);
    return () => clearTimeout(debounce);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marketPosition, marketSearch]);

  useEffect(() => {
    refreshMarket(marketPosition, marketSearch, marketPage).catch(() => setError("A piac betöltése nem sikerült."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marketPage]);

  async function withBusy(key: string, action: () => Promise<void>) {
    setBusy(key);
    setError(null);
    try {
      await action();
    } catch {
      setError("A vásárlás nem sikerült.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      <div className="mb-4 flex gap-2">
        <button
          onClick={() => setSubTab("free-agents")}
          className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${
            subTab === "free-agents" ? "bg-gridiron-accent text-slate-950" : "border border-slate-700 text-slate-300"
          }`}
        >
          Szabadügynökök
        </button>
        <button
          onClick={() => setSubTab("transfers")}
          className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${
            subTab === "transfers" ? "bg-gridiron-accent text-slate-950" : "border border-slate-700 text-slate-300"
          }`}
        >
          Transzferpiac ({transferList?.length ?? 0})
        </button>
      </div>

      {subTab === "free-agents" && (
        <>
          <p className="mb-3 text-xs text-slate-500">
            Valódi NFL-játékosok az ESPN nyilvános adataiból (a fotók az ESPN szervereiről töltődnek be) — az
            OVR-érték viszont játékbeli, generált szám, nem hivatalos értékelés.
          </p>
          <div className="mb-4 flex flex-wrap gap-2">
            <select
              value={marketPosition}
              onChange={(e) => setMarketPosition(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm outline-none focus:border-gridiron-accent"
            >
              {MARKET_POSITIONS.map((pos) => (
                <option key={pos} value={pos}>
                  {pos === "" ? "Összes pozíció" : pos}
                </option>
              ))}
            </select>
            <input
              type="text"
              value={marketSearch}
              onChange={(e) => setMarketSearch(e.target.value)}
              placeholder="Keresés név szerint..."
              className="flex-1 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm outline-none focus:border-gridiron-accent"
            />
          </div>
          {market === null ? (
            <SkeletonCardGrid count={9} />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3" style={{ perspective: 1000 }}>
              {market.map((p, i) => (
                <PlayerCard
                  key={p.id}
                  player={p}
                  index={i}
                  footer={
                    <PriceButton
                      price={p.market_price ?? 0}
                      disabled={team.franchise_capital < (p.market_price ?? 0)}
                      busy={busy === `buy-${p.id}`}
                      onBuy={() =>
                        withBusy(`buy-${p.id}`, async () => {
                          onTeamUpdate(await buyPlayer(p.id));
                          await refreshMarket();
                        })
                      }
                    />
                  }
                />
              ))}
              {market.length === 0 && <p className="text-sm text-slate-500">Nincs a szűrésnek megfelelő szabadügynök.</p>}
            </div>
          )}
          {market !== null && marketTotal > PAGE_SIZE && (
            <div className="mt-4 flex items-center justify-center gap-3 text-sm text-slate-400">
              <button
                disabled={marketPage === 0}
                onClick={() => setMarketPage((p) => Math.max(0, p - 1))}
                className="rounded-lg border border-slate-700 px-3 py-1 disabled:opacity-30"
              >
                Előző
              </button>
              <span>
                {marketPage + 1}. / {Math.max(1, Math.ceil(marketTotal / PAGE_SIZE))}. oldal ({marketTotal} játékos)
              </span>
              <button
                disabled={(marketPage + 1) * PAGE_SIZE >= marketTotal}
                onClick={() => setMarketPage((p) => p + 1)}
                className="rounded-lg border border-slate-700 px-3 py-1 disabled:opacity-30"
              >
                Következő
              </button>
            </div>
          )}
        </>
      )}

      {subTab === "transfers" && (
        <>
          <p className="mb-3 text-xs text-slate-500">
            Más menedzserek által eladásra kínált játékosok. A vételár közvetlenül az eladó csapatnak jár.
          </p>
          {transferList === null ? (
            <SkeletonCardGrid count={6} />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3" style={{ perspective: 1000 }}>
              {transferList.map((p, i) => (
                <PlayerCard
                  key={p.id}
                  player={p}
                  index={i}
                  footer={
                    <PriceButton
                      price={p.asking_price ?? 0}
                      disabled={team.franchise_capital < (p.asking_price ?? 0)}
                      busy={busy === `transfer-${p.id}`}
                      onBuy={() =>
                        withBusy(`transfer-${p.id}`, async () => {
                          onTeamUpdate(await buyTransferListedPlayer(p.id));
                          setTransferList(await listTransferMarket());
                        })
                      }
                    />
                  }
                />
              ))}
              {transferList.length === 0 && (
                <p className="text-sm text-slate-500">Jelenleg nincs transzferlistás játékos.</p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
