import { useState, useEffect, useCallback } from "react";

const SEGMENTS = {
  "3bed": "3 bedroom",
  "4bed": "4 bedroom",
  "6bed": "6 bedroom",
  "8bed_plus": "8+ bedroom",
  "14bed_plus": "14+ bedroom"
};

const INITIAL_COMPS = [
  { id: "1039469824294885969", name: "Arrova Bali Berawa - Luxury 3BR, Rooftop & Jacuzzi", segment: "3bed", url: "https://www.airbnb.com/rooms/1039469824294885969" },
  { id: "998789499934327261", name: "3BR Luxury Bohemian Villa w/ Pool", segment: "3bed", url: "https://www.airbnb.com/rooms/998789499934327261" },
  { id: "1221390320438475482", name: "Villa De Miel | 3BR Pool Canggu Berawa", segment: "3bed", url: "https://www.airbnb.com/rooms/1221390320438475482" },
  { id: "7816774", name: "Villa Brawa 8 - Luxury Gated 3BR", segment: "3bed", url: "https://www.airbnb.com/rooms/7816774" },
  { id: "557467516246068376", name: "3BR Modern Villa AV6 Central Berawa", segment: "3bed", url: "https://www.airbnb.com/rooms/557467516246068376" },
  { id: "1012039362363321230", name: "Villa Harimu - 3BR Modern Berawa", segment: "3bed", url: "https://www.airbnb.com/rooms/1012039362363321230" },
  { id: "1408341853540757156", name: "Villa of Dreams Canggu No.2", segment: "3bed", url: "https://www.airbnb.com/rooms/1408341853540757156" },
  { id: "1038092570588374243", name: "Stunning 3BR Private Villa Berawa Beach", segment: "3bed", url: "https://www.airbnb.com/rooms/1038092570588374243" },
  { id: "38913139", name: "Villa Casa del Sol Berawa/Canggu", segment: "3bed", url: "https://www.airbnb.com/rooms/38913139" },
  { id: "1038698497903204533", name: "Villa Chi Khanh - 4BR Designer Villa Berawa", segment: "4bed", url: "https://www.airbnb.com/rooms/1038698497903204533" },
  { id: "651811709026047336", name: "Maison - 4BR Artistic Designer Villa Canggu", segment: "4bed", url: "https://www.airbnb.com/rooms/651811709026047336" },
  { id: "1503420582527649981", name: "Berawa Beach Canggu Modern 4BR", segment: "4bed", url: "https://www.airbnb.com/rooms/1503420582527649981" },
  { id: "719081356892385552", name: "Berawa Beach Luxury Modern Family Villa", segment: "4bed", url: "https://www.airbnb.com/rooms/719081356892385552" },
  { id: "807785377219843124", name: "Imagine Villa - 4BR Prime Location Canggu", segment: "4bed", url: "https://www.airbnb.com/rooms/807785377219843124" },
  { id: "6716498", name: "Villa Dehesa 1 - 4BR Berawa Beach Gated", segment: "4bed", url: "https://www.airbnb.com/rooms/6716498" },
  { id: "1237275004820875349", name: "Luxurious 4BD Villa w/ Pool & Slide Berawa", segment: "4bed", url: "https://www.airbnb.com/rooms/1237275004820875349" },
  { id: "1563072520099015204", name: "Luxury Villa Aurelia 4BR & Sauna", segment: "4bed", url: "https://www.airbnb.com/rooms/1563072520099015204" },
  { id: "32555786", name: "Private Villa in Canggu Berawa", segment: "4bed", url: "https://www.airbnb.com/rooms/32555786" },
  { id: "1580331401367601465", name: "Mandala Estate - 6BR 2 Pools (2x 3BR)", segment: "6bed", url: "https://www.airbnb.com/rooms/1580331401367601465" },
  { id: "53409617", name: "6BR Canggu: Chef, Lap Pool, Near Beach", segment: "6bed", url: "https://www.airbnb.com/rooms/53409617" },
  { id: "34689243", name: "6BR 2 Pools, Pool Tables, Walk to Beach", segment: "6bed", url: "https://www.airbnb.com/rooms/34689243" },
  { id: "40039509", name: "Canggu Water Bungalows - 7BR Sleeps 16", segment: "8bed_plus", url: "https://www.airbnb.com/rooms/40039509" },
];

const STORAGE_KEY = "comp-tracker-data";

export default function CompetitorDashboard() {
  const [comps, setComps] = useState([]);
  const [priceEntries, setPriceEntries] = useState([]);
  const [activeSegment, setActiveSegment] = useState("3bed");
  const [view, setView] = useState("comps");
  const [showAddForm, setShowAddForm] = useState(false);
  const [newComp, setNewComp] = useState({ name: "", segment: "3bed", url: "", rating: "", reviews: "", price: "" });
  const [editingPrice, setEditingPrice] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const result = await window.storage.get(STORAGE_KEY);
      if (result && result.value) {
        const parsed = JSON.parse(result.value);
        setComps(parsed.comps || INITIAL_COMPS);
        setPriceEntries(parsed.priceEntries || []);
      } else {
        setComps(INITIAL_COMPS);
        setPriceEntries([]);
      }
    } catch {
      setComps(INITIAL_COMPS);
      setPriceEntries([]);
    }
    setLoading(false);
  };

  const saveData = useCallback(async (newComps, newPrices) => {
    try {
      await window.storage.set(STORAGE_KEY, JSON.stringify({ comps: newComps, priceEntries: newPrices }));
    } catch (e) { console.error("Save failed:", e); }
  }, []);

  const addComp = () => {
    if (!newComp.name) return;
    const id = newComp.url.match(/rooms\/(\d+)/)?.[1] || Date.now().toString();
    const comp = { id, name: newComp.name, segment: newComp.segment, url: newComp.url, rating: newComp.rating ? parseFloat(newComp.rating) : null, reviews: newComp.reviews ? parseInt(newComp.reviews) : null };
    const updated = [...comps, comp];
    setComps(updated);
    if (newComp.price) {
      const entry = { id: Date.now().toString(), listingId: id, date: new Date().toISOString().slice(0, 10), price: parseFloat(newComp.price), currency: "USD" };
      const updatedPrices = [...priceEntries, entry];
      setPriceEntries(updatedPrices);
      saveData(updated, updatedPrices);
    } else {
      saveData(updated, priceEntries);
    }
    setNewComp({ name: "", segment: activeSegment, url: "", rating: "", reviews: "", price: "" });
    setShowAddForm(false);
  };

  const removeComp = (id) => {
    const updated = comps.filter(c => c.id !== id);
    const updatedPrices = priceEntries.filter(p => p.listingId !== id);
    setComps(updated);
    setPriceEntries(updatedPrices);
    saveData(updated, updatedPrices);
  };

  const addPriceEntry = (listingId, price, rating, reviews) => {
    const entry = { id: Date.now().toString(), listingId, date: new Date().toISOString().slice(0, 10), price: parseFloat(price), currency: "USD" };
    const updatedPrices = [...priceEntries, entry];
    setPriceEntries(updatedPrices);
    const updatedComps = comps.map(c => {
      if (c.id === listingId) {
        return { ...c, rating: rating ? parseFloat(rating) : c.rating, reviews: reviews ? parseInt(reviews) : c.reviews };
      }
      return c;
    });
    setComps(updatedComps);
    saveData(updatedComps, updatedPrices);
    setEditingPrice(null);
  };

  const getLatestPrice = (listingId) => {
    const entries = priceEntries.filter(p => p.listingId === listingId).sort((a, b) => b.date.localeCompare(a.date));
    return entries[0];
  };

  const getSegmentStats = (segment) => {
    const segComps = comps.filter(c => c.segment === segment);
    const prices = segComps.map(c => getLatestPrice(c.id)?.price).filter(Boolean);
    if (prices.length === 0) return null;
    return {
      count: segComps.length,
      withPrices: prices.length,
      avg: Math.round(prices.reduce((a, b) => a + b, 0) / prices.length),
      min: Math.round(Math.min(...prices)),
      max: Math.round(Math.max(...prices)),
    };
  };

  const filteredComps = comps.filter(c => c.segment === activeSegment);

  if (loading) return <div style={{ padding: "2rem", color: "var(--color-text-secondary)" }}>Loading...</div>;

  return (
    <div style={{ fontFamily: "var(--font-sans)", color: "var(--color-text-primary)" }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: "1.5rem" }}>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 500, margin: 0 }}>Berawa comp tracker</h2>
          <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "4px 0 0" }}>
            {comps.length} listings tracked · {priceEntries.length} price points recorded
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setView("comps")} style={{ background: view === "comps" ? "var(--color-background-secondary)" : "transparent", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-md)", padding: "6px 14px", fontSize: 13, cursor: "pointer", color: "var(--color-text-primary)" }}>Listings</button>
          <button onClick={() => setView("overview")} style={{ background: view === "overview" ? "var(--color-background-secondary)" : "transparent", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-md)", padding: "6px 14px", fontSize: 13, cursor: "pointer", color: "var(--color-text-primary)" }}>Overview</button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 6, marginBottom: "1.5rem", flexWrap: "wrap" }}>
        {Object.entries(SEGMENTS).map(([key, label]) => {
          const count = comps.filter(c => c.segment === key).length;
          return (
            <button key={key} onClick={() => setActiveSegment(key)} style={{
              background: activeSegment === key ? "var(--color-text-primary)" : "transparent",
              color: activeSegment === key ? "var(--color-background-primary)" : "var(--color-text-secondary)",
              border: "0.5px solid " + (activeSegment === key ? "var(--color-text-primary)" : "var(--color-border-tertiary)"),
              borderRadius: "var(--border-radius-md)", padding: "6px 14px", fontSize: 13, cursor: "pointer", transition: "all 0.15s"
            }}>
              {label} ({count})
            </button>
          );
        })}
      </div>

      {view === "overview" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12, marginBottom: "1.5rem" }}>
          {Object.keys(SEGMENTS).map(seg => {
            const stats = getSegmentStats(seg);
            return (
              <div key={seg} style={{ background: "var(--color-background-secondary)", borderRadius: "var(--border-radius-md)", padding: "1rem" }}>
                <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 4 }}>{SEGMENTS[seg]}</div>
                {stats ? (
                  <>
                    <div style={{ fontSize: 22, fontWeight: 500 }}>${stats.avg}</div>
                    <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 4 }}>
                      ${stats.min}–${stats.max} · {stats.withPrices}/{stats.count} priced
                    </div>
                  </>
                ) : (
                  <div style={{ fontSize: 14, color: "var(--color-text-secondary)" }}>No prices yet</div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {view === "comps" && (
        <>
          <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
            <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 70px 70px 80px 40px", gap: 12, padding: "8px 12px", fontSize: 12, color: "var(--color-text-secondary)", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
              <span>Listing</span>
              <span style={{ textAlign: "right" }}>Rating</span>
              <span style={{ textAlign: "right" }}>Reviews</span>
              <span style={{ textAlign: "right" }}>Price</span>
              <span></span>
            </div>

            {filteredComps.map(comp => {
              const latest = getLatestPrice(comp.id);
              const isEditing = editingPrice === comp.id;
              return (
                <div key={comp.id}>
                  <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 70px 70px 80px 40px", gap: 12, padding: "10px 12px", borderBottom: "0.5px solid var(--color-border-tertiary)", alignItems: "center", fontSize: 14 }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontWeight: 500, fontSize: 13 }}>
                        {comp.url ? <a href={comp.url} style={{ color: "var(--color-text-info)", textDecoration: "none" }}>{comp.name}</a> : comp.name}
                      </div>
                      {latest && <div style={{ fontSize: 11, color: "var(--color-text-secondary)", marginTop: 2 }}>Updated {latest.date}</div>}
                    </div>
                    <div style={{ textAlign: "right", fontSize: 13 }}>{comp.rating || "—"}</div>
                    <div style={{ textAlign: "right", fontSize: 13 }}>{comp.reviews || "—"}</div>
                    <div style={{ textAlign: "right", fontWeight: 500, fontSize: 13, cursor: "pointer", color: latest ? "var(--color-text-primary)" : "var(--color-text-info)" }} onClick={() => setEditingPrice(isEditing ? null : comp.id)}>
                      {latest ? `$${Math.round(latest.price)}` : "+ price"}
                    </div>
                    <button onClick={() => removeComp(comp.id)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 16, color: "var(--color-text-secondary)", padding: 0, lineHeight: 1 }} title="Remove">x</button>
                  </div>
                  {isEditing && <PriceInput listingId={comp.id} currentRating={comp.rating} currentReviews={comp.reviews} onSave={addPriceEntry} onCancel={() => setEditingPrice(null)} />}
                </div>
              );
            })}
          </div>

          {!showAddForm ? (
            <button onClick={() => { setShowAddForm(true); setNewComp(n => ({ ...n, segment: activeSegment })); }} style={{ marginTop: 12, background: "transparent", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-md)", padding: "8px 16px", fontSize: 13, cursor: "pointer", color: "var(--color-text-secondary)", width: "100%" }}>
              + Add listing to {SEGMENTS[activeSegment]}
            </button>
          ) : (
            <div style={{ marginTop: 12, background: "var(--color-background-secondary)", borderRadius: "var(--border-radius-lg)", padding: "1rem" }}>
              <div style={{ display: "grid", gap: 8 }}>
                <input placeholder="Listing name" value={newComp.name} onChange={e => setNewComp(n => ({ ...n, name: e.target.value }))} style={{ fontSize: 14 }} />
                <input placeholder="Airbnb URL (paste full link)" value={newComp.url} onChange={e => setNewComp(n => ({ ...n, url: e.target.value }))} style={{ fontSize: 14 }} />
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                  <input placeholder="Rating" value={newComp.rating} onChange={e => setNewComp(n => ({ ...n, rating: e.target.value }))} style={{ fontSize: 14 }} />
                  <input placeholder="Reviews" value={newComp.reviews} onChange={e => setNewComp(n => ({ ...n, reviews: e.target.value }))} style={{ fontSize: 14 }} />
                  <input placeholder="Price/night ($)" value={newComp.price} onChange={e => setNewComp(n => ({ ...n, price: e.target.value }))} style={{ fontSize: 14 }} />
                </div>
                <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                  <button onClick={() => setShowAddForm(false)} style={{ fontSize: 13, padding: "6px 14px", background: "transparent", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-md)", cursor: "pointer", color: "var(--color-text-secondary)" }}>Cancel</button>
                  <button onClick={addComp} style={{ fontSize: 13, padding: "6px 14px", background: "var(--color-text-primary)", color: "var(--color-background-primary)", border: "none", borderRadius: "var(--border-radius-md)", cursor: "pointer" }}>Add</button>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      <div style={{ marginTop: "2rem", padding: "1rem", background: "var(--color-background-secondary)", borderRadius: "var(--border-radius-md)", fontSize: 13, color: "var(--color-text-secondary)" }}>
        <strong style={{ fontWeight: 500, color: "var(--color-text-primary)" }}>How to use this tracker</strong>
        <ol style={{ margin: "8px 0 0", paddingLeft: 20, lineHeight: 1.8 }}>
          <li>Review the pre-loaded comp set — remove any that aren't true competitors, add ones that are</li>
          <li>Click a listing's price column to log the current nightly rate you see on Airbnb</li>
          <li>Update prices weekly to build trend data over time</li>
          <li>For automated daily scraping, run the Python script on your machine</li>
        </ol>
      </div>
    </div>
  );
}

function PriceInput({ listingId, currentRating, currentReviews, onSave, onCancel }) {
  const [price, setPrice] = useState("");
  const [rating, setRating] = useState(currentRating?.toString() || "");
  const [reviews, setReviews] = useState(currentReviews?.toString() || "");
  return (
    <div style={{ display: "flex", gap: 8, padding: "8px 12px", background: "var(--color-background-secondary)", alignItems: "center" }}>
      <input placeholder="$/night" value={price} onChange={e => setPrice(e.target.value)} style={{ width: 80, fontSize: 13 }} autoFocus />
      <input placeholder="Rating" value={rating} onChange={e => setRating(e.target.value)} style={{ width: 60, fontSize: 13 }} />
      <input placeholder="Reviews" value={reviews} onChange={e => setReviews(e.target.value)} style={{ width: 60, fontSize: 13 }} />
      <button onClick={() => { if (price) onSave(listingId, price, rating, reviews); }} style={{ fontSize: 12, padding: "4px 12px", background: "var(--color-text-primary)", color: "var(--color-background-primary)", border: "none", borderRadius: "var(--border-radius-md)", cursor: "pointer" }}>Save</button>
      <button onClick={onCancel} style={{ fontSize: 12, padding: "4px 12px", background: "transparent", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-md)", cursor: "pointer", color: "var(--color-text-secondary)" }}>Cancel</button>
    </div>
  );
}
