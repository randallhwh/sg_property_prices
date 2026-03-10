import { useState, useMemo } from "react";
import {
  ComposedChart, Bar, Line, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer, ReferenceArea
} from "recharts";

// ─── DATA ────────────────────────────────────────────────────────────────────
// URA PPI annual % change (all private residential, 2009-Q1 = 100 base)
// Forecast sourcing:
//   2015–2025: Published consensus from CBRE, Knight Frank, DBS, PropNex, OrangeTee, ERA
//   1998–2014: RECONSTRUCTED from contemporaneous analyst commentary, media reports,
//              DTZ/JLL/Knight Frank/CBRE annual outlooks. Marked with [R] in consensus field.
//              Should be treated as indicative, not verbatim published ranges.
const RAW = [
  // ── AFC CYCLE ─────────────────────────────────────────────────────────────
  // 1997: Market peaked; late-1997 AFC hit. By start of 1998, analysts knew a correction was coming
  // but magnitude was wildly underestimated. DTZ/JLL forecasts: -10 to -15% for 1998.
  { year: 1998, actual: -44.7, regime: "Crisis",
    event: "Asian Financial Crisis — worst single-year crash on record",
    forecastMid: -12.0, forecastLow: -15.0, forecastHigh: -8.0,
    consensus: "[R] DTZ/JLL: orderly -8 to -15% correction expected. Actual collapse -45% shocked market." },

  // 1999: Post-AFC, analysts split between further falls (-5%) and stabilisation (0%).
  // Actual: small further decline, broadly in range.
  { year: 1999, actual: -1.9, regime: "Recovery",
    event: "Post-AFC trough; slow stabilisation",
    forecastMid: -3.0, forecastLow: -8.0, forecastHigh: 0.0,
    consensus: "[R] Analysts expected continued weakness -3 to -8%; actual -1.9% beat consensus." },

  // 2000: Dot-com boom boosted sentiment early in year; analysts optimistic about recovery (+2 to +5%).
  // Dot-com bust in H2 reversed the outlook; actual flat/down.
  { year: 2000, actual: -2.0, regime: "Recovery",
    event: "Dot-com bust reversed early recovery optimism",
    forecastMid: 2.5, forecastLow: 0.0, forecastHigh: 5.0,
    consensus: "[R] Early 2000 consensus: recovery +2 to +5%. Dot-com bust in H2 was not priced in." },

  // 2001: 9/11 + tech recession. Pre-9/11 forecasts were flat to mild positive.
  // Post-9/11 revised to -5 to -10%. Actual -10% = bottom of revised range.
  { year: 2001, actual: -10.0, regime: "Crisis",
    event: "9/11 shock + dot-com recession",
    forecastMid: -3.0, forecastLow: -6.0, forecastHigh: 0.0,
    consensus: "[R] Pre-year consensus: flat to -3%. Post-9/11 revised to -5 to -10%. Actual hit revised floor." },

  // 2002: Continued weakness. Analysts mostly expected -2 to -5% given weak global growth.
  { year: 2002, actual: -3.4, regime: "Bear",
    event: "Continued post-dot-com/9/11 weakness",
    forecastMid: -3.0, forecastLow: -5.0, forecastHigh: -1.0,
    consensus: "[R] Consensus: continued decline -2 to -5%. Actual -3.4% in line with expectations." },

  // 2003: SARS outbreak Feb–May 2003 was a significant unknown. Pre-SARS analysts: flat to slight recovery.
  // Post-SARS revised negative. Actual -3.2% = mild miss to the downside vs pre-year forecasts.
  { year: 2003, actual: -3.2, regime: "Bear",
    event: "SARS outbreak derailed nascent recovery",
    forecastMid: 1.0, forecastLow: -1.0, forecastHigh: 3.0,
    consensus: "[R] Pre-year: flat to +3% recovery. SARS hit in Feb was unpredicted; actual -3.2% big miss." },

  // ── PRE-GFC BULL ──────────────────────────────────────────────────────────
  // 2004: Recovery widely expected after 5 bad years. Consensus +2 to +5%. Actual +3.6% in range.
  { year: 2004, actual: 3.6, regime: "Bull",
    event: "Recovery begins; global growth accelerates",
    forecastMid: 3.0, forecastLow: 1.0, forecastHigh: 5.0,
    consensus: "[R] DTZ/JLL: recovery +2 to +5% expected. Actual +3.6% in range." },

  // 2005: Bull confirmed. Analysts +3 to +7%. Actual +3.9% at lower end.
  { year: 2005, actual: 3.9, regime: "Bull",
    event: "Global liquidity boom; low rates supportive",
    forecastMid: 5.0, forecastLow: 3.0, forecastHigh: 8.0,
    consensus: "[R] Consensus: +3 to +8% continued recovery. Actual +3.9% at low end of range." },

  // 2006: Acceleration. Analysts forecasting +5 to +10%. Actual +10.2% at top of range.
  { year: 2006, actual: 10.2, regime: "Bull",
    event: "Credit boom accelerates; en-bloc cycle heats up",
    forecastMid: 7.0, forecastLow: 4.0, forecastHigh: 10.0,
    consensus: "[R] Bullish consensus +5 to +10%. Actual +10.2% hit top of range; euphoria building." },

  // 2007: Extreme euphoria. Even bullish analysts only pencilled in +10 to +15%.
  // Actual +31.2% was completely off the charts — the single biggest miss in the dataset.
  { year: 2007, actual: 31.2, regime: "Bull",
    event: "Peak — unprecedented en-bloc + credit frenzy",
    forecastMid: 12.0, forecastLow: 8.0, forecastHigh: 18.0,
    consensus: "[R] Most bullish houses: +10 to +18%. Actual +31.2% was the biggest upside miss on record." },

  // ── GFC ───────────────────────────────────────────────────────────────────
  // 2008: Pre-year forecasts were +5 to +10% (still bullish after 2007 peak).
  // GFC erupted Sep 2008 (Lehman). Mid-year revised to -10 to -15%. Actual -24.9% shocked everyone.
  { year: 2008, actual: -24.9, regime: "Crisis",
    event: "Global Financial Crisis — Lehman collapse Sep 2008",
    forecastMid: 5.0, forecastLow: 2.0, forecastHigh: 10.0,
    consensus: "[R] Pre-year: +5 to +10%. GFC erupted mid-year; revised to -10 to -15%. Actual -25% shocked all." },

  // ── POST-GFC RECOVERY ─────────────────────────────────────────────────────
  // 2009: Post-GFC, consensus was -5 to -15% (expecting continued falls).
  // Massive global stimulus + near-zero rates drove surprise +1.8%.
  { year: 2009, actual: 1.8, regime: "Recovery",
    event: "Massive QE + near-zero rates; surprise recovery",
    forecastMid: -8.0, forecastLow: -15.0, forecastHigh: -2.0,
    consensus: "[R] Consensus: -5 to -15% further decline. Actual +1.8% was a major positive surprise." },

  // 2010: Post-GFC boom. Even after 2009's surprise, few forecast +15%+.
  // Consensus: +5 to +10%. Actual +17.6% blew past all forecasts; forced Aug 2010 cooling.
  { year: 2010, actual: 17.6, regime: "Bull",
    event: "Post-GFC boom; government forced into Aug 2010 cooling",
    forecastMid: 7.0, forecastLow: 4.0, forecastHigh: 10.0,
    consensus: "[R] Most houses: +5 to +10%. Actual +17.6% was 2nd biggest upside miss; triggered cooling." },

  // 2011: Multiple cooling rounds (Jan, Aug, Dec 2011). Analysts: +5 to +10% continuation.
  // Actual +5.9% at low end — cooling was more effective than expected.
  { year: 2011, actual: 5.9, regime: "Cooling",
    event: "Three cooling rounds in Jan, Aug, Dec 2011",
    forecastMid: 7.0, forecastLow: 4.0, forecastHigh: 12.0,
    consensus: "[R] Consensus: +5 to +12% despite cooling. Actual +5.9% at low end; cooling starting to bite." },

  // 2012: ABSD introduced Jan 2012. Analysts split: bears said flat/negative, bulls said +3 to +5%.
  // Consensus mid ~+3%. Actual +2.8% broadly in range.
  { year: 2012, actual: 2.8, regime: "Cooling",
    event: "ABSD introduced Jan 2012; foreign buying chilled",
    forecastMid: 3.0, forecastLow: 0.0, forecastHigh: 5.0,
    consensus: "[R] Post-ABSD consensus: +1 to +5% moderation. Actual +2.8% in line." },

  // 2013: TDSR introduced Jun 2013 was widely flagged. Pre-TDSR forecasts: +2 to +5%.
  // Post-TDSR actual: +1.1%, below consensus but not by much.
  { year: 2013, actual: 1.1, regime: "Cooling",
    event: "TDSR introduced Jun 2013; leverage constrained",
    forecastMid: 3.0, forecastLow: 1.0, forecastHigh: 5.0,
    consensus: "[R] Consensus before TDSR: +2 to +5%. Post-TDSR year outturn +1.1% below range." },

  // 2014: JLL's Stuart Crow: -8 to -10% per year through 2015. Knight Frank: continued falls.
  // Consensus formed around -3 to -7%. Actual -4.0% in middle of range.
  { year: 2014, actual: -4.0, regime: "Bear",
    event: "Cooling measures fully bite; JLL flagged -8-10%/yr",
    forecastMid: -5.0, forecastLow: -8.0, forecastHigh: -2.0,
    consensus: "[R] JLL: -8 to -10%/yr; Knight Frank: sustained decline. Consensus -3 to -8%. Actual -4% in range." },

  // ── PUBLISHED CONSENSUS ERA (2015+) ───────────────────────────────────────
  { year: 2015, actual: -3.7, regime: "Bear",
    event: "TDSR + ABSD fully felt; market in sustained bear",
    forecastMid: -1.5, forecastLow: -3.0, forecastHigh: 0.0,
    consensus: "Mild decline (-1 to -3%); actual -3.7% below range" },

  { year: 2016, actual: -3.1, regime: "Bear",
    event: "Prolonged correction; market bottoming",
    forecastMid: -1.5, forecastLow: -3.0, forecastHigh: 0.0,
    consensus: "Stabilisation / flat (-1 to 0%); actual -3.1% missed" },

  { year: 2017, actual: 1.1, regime: "Recovery",
    event: "Slow recovery begins; GLS bids pick up",
    forecastMid: 0.5, forecastLow: -1.0, forecastHigh: 2.0,
    consensus: "Flat to marginal recovery (0 to +1%)" },

  { year: 2018, actual: 7.9, regime: "Bull",
    event: "Surprise cooling measures Jul 2018",
    forecastMid: 3.0, forecastLow: 1.0, forecastHigh: 5.0,
    consensus: "Moderate recovery (+2 to +5%); actual +7.9% far beat" },

  { year: 2019, actual: 2.7, regime: "Cooling",
    event: "Post-cooling moderation; measured growth",
    forecastMid: 2.0, forecastLow: 0.0, forecastHigh: 4.0,
    consensus: "Modest growth (+1 to +3%)" },

  { year: 2020, actual: 2.2, regime: "Recovery",
    event: "COVID — rates crash; defied all recession forecasts",
    forecastMid: -2.5, forecastLow: -5.0, forecastHigh: 0.0,
    consensus: "Decline (-2 to -5%) given COVID; actual +2.2% massive beat" },

  { year: 2021, actual: 10.6, regime: "Bull",
    event: "Post-COVID boom; highest since 2007",
    forecastMid: 4.0, forecastLow: 2.0, forecastHigh: 6.0,
    consensus: "Recovery (+3 to +6%); actual +10.6% far beat consensus" },

  { year: 2022, actual: 8.6, regime: "Bull",
    event: "Rate hikes begin; Sep 2022 cooling round",
    forecastMid: 5.5, forecastLow: 3.0, forecastHigh: 8.0,
    consensus: "Continued growth (+4 to +8%); actual at top of range" },

  { year: 2023, actual: 6.8, regime: "Cooling",
    event: "ABSD raised to 60% for foreigners Apr 2023",
    forecastMid: 5.5, forecastLow: 3.0, forecastHigh: 8.0,
    consensus: "Moderate growth (+4 to +7%)" },

  { year: 2024, actual: 3.9, regime: "Stable",
    event: "High rate environment; affordability drag",
    forecastMid: 5.0, forecastLow: 3.0, forecastHigh: 7.0,
    consensus: "Growth (+4 to +7%); actual 3.9% below mid" },

  { year: 2025, actual: 3.4, regime: "Stable",
    event: "Tariff shock paused market; rate cuts support",
    forecastMid: 3.0, forecastLow: 1.0, forecastHigh: 5.0,
    consensus: "Moderation (+1 to +5%); DBS 1-2%, others 3-5%" },
];

// ─── REGIME DETECTION FRAMEWORK ─────────────────────────────────────────────
const REGIME_SIGNALS = [
  {
    name: "Interest Rate Inflection",
    description: "Central bank pivots (hike→cut or cut→hike) historically lead price regime changes by 2–4 quarters in Singapore. SORA/SOR movements are the most reliable leading indicator.",
    weight: "High",
    examples: "2009 (GFC cuts → 2010 boom), 2022 (hikes → 2024 slowdown), 2024 (cuts → 2025 resilience)",
    icon: "📈"
  },
  {
    name: "Policy Intervention Signal",
    description: "New ABSD rounds, TDSR changes, or LTV tightening. Government typically acts after 3+ consecutive quarters of >2% QoQ gains. Watch for budget statements and MAS consultations.",
    weight: "High",
    examples: "2013 TDSR → 2014-16 correction. 2018 surprise cooling → 2019 moderation. 2023 ABSD 60% → foreign demand collapse",
    icon: "🏛️"
  },
  {
    name: "Transaction Velocity Divergence",
    description: "New home sales volumes leading price by ~2 quarters. Volume surges (>3,000 units/quarter) ahead of price. Volume collapse before price correction. Currently >10,000 units in 2025.",
    weight: "Medium",
    examples: "2007 volume peak preceded 2008 crash. 2021 13,000 units preceded 2022 peak. Volume cooling in 2014 preceded 2015-16 decline",
    icon: "🔄"
  },
  {
    name: "Developer Land Bid Premiums",
    description: "GLS tender price-to-reserve ratios >120% signal developer euphoria and future price support. Ratios <105% signal risk-off. Tracks 12–18 months ahead of completions.",
    weight: "Medium",
    examples: "2017-18 aggressive GLS bids preceded 2018 price surge. 2020 cautious bids reflected COVID uncertainty before surprise recovery",
    icon: "🏗️"
  },
  {
    name: "HDB Resale/Private Price Gap",
    description: "Narrowing gap signals HDB upgrader demand approaching saturation or private unaffordability. Wide gap = pent-up upgrader demand. Current gap narrowing is a mild caution signal.",
    weight: "Medium",
    examples: "2010-12: gap narrowed rapidly as upgraders flooded private market → cooling response. 2024-25: gap narrowing again",
    icon: "🏠"
  },
  {
    name: "Foreign Capital Flow Proxies",
    description: "Singapore bank non-resident deposit growth, luxury CCR transactions by foreigners, and USD/SGD direction. Pre-2023 ABSD, foreign flows were ~15-20% of CCR demand.",
    weight: "Low (post-2023)",
    examples: "2011-13: surge in foreign buyers (China, Indonesia) amplified CCR prices before ABSD targeted foreigners. Now structurally muted at 60% ABSD",
    icon: "🌏"
  },
  {
    name: "Mortgage Credit Conditions",
    description: "MAS housing loan data (value of new loans granted) and TDSR headroom. Credit expansion >15% YoY typically precedes price acceleration. Loan data lags price by ~1Q.",
    weight: "Medium",
    examples: "2024 housing loans +15% YoY supported 2025 demand. 2012-13 loan growth slowed post-ABSD/TDSR, preceding 2014-16 correction",
    icon: "💳"
  },
  {
    name: "Completion Pipeline vs Demand",
    description: "Units completing in next 4–6 quarters vs. household formation rate (~20K/yr). Supply glut (>15K completions) suppresses rents first, then prices. Current pipeline is thin (5,249 in 2025).",
    weight: "Medium",
    examples: "2016-17: large completions from 2013-14 launches added supply pressure. 2023-25: thin completions (post-COVID delays) supported prices",
    icon: "📦"
  },
];

// Regime colour map
const REGIME_COLOR = {
  Bull:     "#22c55e",
  Crisis:   "#ef4444",
  Bear:     "#f97316",
  Recovery: "#60a5fa",
  Cooling:  "#a78bfa",
  Stable:   "#94a3b8",
};

const MISS_COLOR = {
  "Far beat":   "#22c55e",
  "Beat":       "#86efac",
  "In range":   "#94a3b8",
  "Top range":  "#fbbf24",
  "Miss":       "#f87171",
  "Far miss":   "#ef4444",
};

function getMiss(row) {
  if (row.actual > row.forecastHigh + 2) return "Far beat";
  if (row.actual > row.forecastHigh) return "Beat";
  if (row.actual < row.forecastLow - 2) return "Far miss";
  if (row.actual < row.forecastLow) return "Miss";
  if (row.actual >= row.forecastHigh - 0.5) return "Top range";
  return "In range";
}

const data = RAW.map(r => ({ ...r, miss: getMiss(r), rangeBand: r.forecastHigh !== null ? r.forecastHigh - r.forecastLow : null, rangeBase: r.forecastLow }));

// ─── COMPONENTS ──────────────────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const row = data.find(d => d.year === label);
  if (!row) return null;
  return (
    <div style={{ background: "#0a1120", border: `1px solid ${REGIME_COLOR[row.regime]}55`, borderRadius: 8, padding: "12px 16px", maxWidth: 280, fontFamily: "'IBM Plex Mono', monospace", fontSize: 11 }}>
      <div style={{ fontSize: 16, fontWeight: 700, color: "#f1f5f9", marginBottom: 6 }}>{label}</div>
      <div style={{ color: REGIME_COLOR[row.regime], marginBottom: 4 }}>▶ {row.regime} regime</div>
      <div style={{ color: "#94a3b8", marginBottom: 2 }}>{row.event}</div>
      <div style={{ marginTop: 8, color: row.actual >= 0 ? "#fbbf24" : "#f87171", fontWeight: 700, fontSize: 15 }}>
        Actual: {row.actual > 0 ? "+" : ""}{row.actual}%
      </div>
      {row.forecastMid !== null && (
        <>
          <div style={{ color: "#3b82f6", marginTop: 2 }}>Consensus: {row.forecastLow > 0 ? "+" : ""}{row.forecastLow}% to {row.forecastHigh > 0 ? "+" : ""}{row.forecastHigh}%</div>
          <div style={{ color: MISS_COLOR[row.miss], marginTop: 4, fontWeight: 600 }}>{row.miss}</div>
        </>
      )}
    </div>
  );
};

// ─── MAIN ─────────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState("chart");
  const [selectedYear, setSelectedYear] = useState(null);
  const [signalOpen, setSignalOpen] = useState(null);

  const selectedRow = selectedYear ? data.find(d => d.year === selectedYear) : null;

  const consensusData = data;
  const avgDelta = consensusData.reduce((s, d) => s + (d.actual - d.forecastMid), 0) / consensusData.length;
  const beatCount = consensusData.filter(d => d.actual > d.forecastHigh).length;
  const inRangeCount = consensusData.filter(d => d.actual >= d.forecastLow && d.actual <= d.forecastHigh).length;
  const missCount = consensusData.filter(d => d.actual < d.forecastLow).length;

  // Regime blocks for shading
  const regimeBlocks = useMemo(() => {
    const blocks = [];
    let cur = null;
    data.forEach((d, i) => {
      if (!cur || d.regime !== cur.regime) {
        if (cur) { cur.end = data[i - 1].year; blocks.push(cur); }
        cur = { regime: d.regime, start: d.year, end: d.year };
      }
    });
    if (cur) { cur.end = data[data.length - 1].year; blocks.push(cur); }
    return blocks;
  }, []);

  const styles = {
    root: { minHeight: "100vh", background: "#060c18", fontFamily: "'IBM Plex Sans', 'DM Sans', sans-serif", color: "#f1f5f9", padding: "28px 20px" },
    container: { maxWidth: 1180, margin: "0 auto" },
    tab: (active) => ({
      padding: "7px 18px", borderRadius: 6, fontSize: 12, fontWeight: 600,
      letterSpacing: "0.5px", cursor: "pointer", border: "1px solid",
      background: active ? "#1e3a5f" : "transparent",
      borderColor: active ? "#3b82f6" : "#1e293b",
      color: active ? "#60a5fa" : "#475569",
      transition: "all 0.15s",
    }),
    card: { background: "#0d1a2d", border: "1px solid #1e2d45", borderRadius: 10, padding: "14px 18px" },
    pill: (color) => ({
      display: "inline-flex", alignItems: "center", gap: 5,
      padding: "2px 9px", borderRadius: 20, fontSize: 10, fontWeight: 700,
      background: color + "20", border: `1px solid ${color}44`, color,
    }),
  };

  return (
    <div style={styles.root}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: #060c18; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
        .trow:hover { background: #0d1a2d !important; cursor: pointer; }
        .signal-card { transition: all 0.2s; }
        .signal-card:hover { border-color: #3b82f688 !important; background: #0d1a2d !important; }
      `}</style>

      <div style={styles.container}>
        {/* Header */}
        <div style={{ marginBottom: 28 }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 16, justifyContent: "space-between", flexWrap: "wrap" }}>
            <div>
              <div style={{ fontSize: 10, letterSpacing: "3px", textTransform: "uppercase", color: "#334155", marginBottom: 4 }}>
                URA Private Residential Property Price Index
              </div>
              <h1 style={{ fontSize: 24, fontWeight: 700, color: "#f1f5f9", lineHeight: 1.1 }}>
                Singapore Property: 28-Year History
              </h1>
              <p style={{ fontSize: 12, color: "#475569", marginTop: 5 }}>
                Annual % change · Forecast vs Actual (2015–2025) · Regime classification · Regime-shift detection framework
              </p>
            </div>
            {/* Summary pills */}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
              {[
                { label: "Avg beat vs mid", val: `${avgDelta > 0 ? "+" : ""}${avgDelta.toFixed(1)}pp`, color: "#22c55e" },
                { label: "Beat range", val: `${beatCount}/${consensusData.length}`, color: "#22c55e" },
                { label: "In range", val: `${inRangeCount}/${consensusData.length}`, color: "#60a5fa" },
                { label: "Missed", val: `${missCount}/${consensusData.length}`, color: "#f87171" },
              ].map(s => (
                <div key={s.label} style={{ ...styles.card, padding: "8px 14px", textAlign: "center" }}>
                  <div style={{ fontSize: 10, color: "#334155", textTransform: "uppercase", letterSpacing: "1px" }}>{s.label}</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: s.color, fontFamily: "'IBM Plex Mono', monospace" }}>{s.val}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
          {[["chart", "📊 Price History"], ["table", "📋 Data Table"], ["signals", "🔍 Regime Signals"]].map(([id, label]) => (
            <button key={id} style={styles.tab(tab === id)} onClick={() => setTab(id)}>{label}</button>
          ))}
        </div>

        {/* ── TAB: CHART ── */}
        {tab === "chart" && (
          <>
            {/* Regime legend */}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14 }}>
              {Object.entries(REGIME_COLOR).map(([r, c]) => (
                <div key={r} style={styles.pill(c)}>
                  <div style={{ width: 6, height: 6, borderRadius: "50%", background: c }} />
                  {r}
                </div>
              ))}
              <div style={{ ...styles.pill("#3b82f6"), marginLeft: "auto" }}>
                <div style={{ width: 14, height: 2, background: "#3b82f6", borderTop: "2px dashed #3b82f6" }} />
                Consensus band (2015+)
              </div>
            </div>

            <div style={{ ...styles.card, padding: "20px 12px 12px", marginBottom: 16 }}>
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
                  onClick={(e) => e?.activePayload && setSelectedYear(e.activePayload[0]?.payload?.year)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#0f1e35" />
                  {/* Regime shading */}
                  {regimeBlocks.map((b, i) => (
                    <ReferenceArea
                      key={i}
                      x1={b.start} x2={b.end}
                      fill={REGIME_COLOR[b.regime]}
                      fillOpacity={0.04}
                    />
                  ))}
                  <XAxis dataKey="year" tick={{ fill: "#334155", fontSize: 10, fontFamily: "IBM Plex Mono" }}
                    axisLine={{ stroke: "#0f1e35" }} tickLine={false} interval={1}
                    angle={-45} textAnchor="end" height={45} />
                  <YAxis tick={{ fill: "#334155", fontSize: 10, fontFamily: "IBM Plex Mono" }}
                    axisLine={false} tickLine={false}
                    tickFormatter={v => `${v > 0 ? "+" : ""}${v}%`}
                    domain={[-50, 40]} />
                  <ReferenceLine y={0} stroke="#1e3a5f" strokeWidth={1.5} />
                  <Tooltip content={<CustomTooltip />} />

                  {/* Forecast band base (invisible, for stacking) */}
                  <Bar dataKey="rangeBase" stackId="band" fill="transparent" legendType="none" />
                  {/* Forecast band */}
                  <Bar dataKey="rangeBand" stackId="band" fill="#3b82f618" stroke="#3b82f630"
                    strokeWidth={1} name="Forecast Range" radius={[2, 2, 0, 0]} />

                  {/* Forecast mid line */}
                  <Line type="monotone" dataKey="forecastMid"
                    stroke="#3b82f6" strokeWidth={1.5} strokeDasharray="4 3"
                    dot={false} name="Consensus Mid"
                    connectNulls={false} />

                  {/* Actual */}
                  <Line
                    type="monotone" dataKey="actual"
                    stroke="#fbbf24" strokeWidth={2.5}
                    dot={(props) => {
                      const { cx, cy, payload } = props;
                      const c = REGIME_COLOR[payload.regime] || "#fbbf24";
                      const isSelected = payload.year === selectedYear;
                      return (
                        <circle key={payload.year} cx={cx} cy={cy}
                          r={isSelected ? 7 : 4}
                          fill={c} stroke={isSelected ? "#f1f5f9" : "#060c18"}
                          strokeWidth={isSelected ? 2 : 1.5}
                          style={{ cursor: "pointer" }} />
                      );
                    }}
                    name="Actual (URA PPI)"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Selected year detail */}
            {selectedRow && (
              <div style={{
                ...styles.card,
                borderColor: REGIME_COLOR[selectedRow.regime] + "55",
                display: "flex", gap: 20, alignItems: "flex-start", flexWrap: "wrap"
              }}>
                <div style={{ minWidth: 70 }}>
                  <div style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 28, fontWeight: 700, color: "#f1f5f9" }}>{selectedRow.year}</div>
                  <div style={styles.pill(REGIME_COLOR[selectedRow.regime])}>{selectedRow.regime}</div>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, color: "#60a5fa", marginBottom: 4 }}>{selectedRow.event}</div>
                  <div style={{ display: "flex", gap: 20, flexWrap: "wrap", marginTop: 6 }}>
                    <div>
                      <div style={{ fontSize: 10, color: "#334155", textTransform: "uppercase" }}>Actual</div>
                      <div style={{ fontFamily: "'IBM Plex Mono'", fontSize: 22, fontWeight: 700, color: selectedRow.actual >= 0 ? "#fbbf24" : "#f87171" }}>
                        {selectedRow.actual > 0 ? "+" : ""}{selectedRow.actual}%
                      </div>
                    </div>
                  {selectedRow.forecastMid !== null && (
                      <>
                        <div>
                          <div style={{ fontSize: 10, color: "#334155", textTransform: "uppercase" }}>Forecast range</div>
                          <div style={{ fontFamily: "'IBM Plex Mono'", fontSize: 16, color: "#3b82f6", marginTop: 4 }}>
                            {selectedRow.forecastLow > 0 ? "+" : ""}{selectedRow.forecastLow}% to {selectedRow.forecastHigh > 0 ? "+" : ""}{selectedRow.forecastHigh}%
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: 10, color: "#334155", textTransform: "uppercase" }}>Delta vs mid</div>
                          <div style={{ fontFamily: "'IBM Plex Mono'", fontSize: 16, marginTop: 4, color: MISS_COLOR[selectedRow.miss] }}>
                            {(selectedRow.actual - selectedRow.forecastMid) > 0 ? "+" : ""}{(selectedRow.actual - selectedRow.forecastMid).toFixed(1)}pp
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: 10, color: "#334155", textTransform: "uppercase" }}>Verdict</div>
                          <div style={{ ...styles.pill(MISS_COLOR[selectedRow.miss]), marginTop: 6, fontSize: 12 }}>{selectedRow.miss}</div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Cycle summary */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginTop: 16 }}>
              {[
                { title: "AFC → SARS (1998–2003)", desc: "Two deep crises bookending a dead-cat recovery. AFC wiped 45% in one year. 9/11 + SARS compounded the multi-year bear.", color: "#ef4444" },
                { title: "Pre-GFC Bull (2004–2007)", desc: "Global credit super-cycle. 2007 +31% was the all-time single-year peak, fuelled by regional capital inflows and leverage.", color: "#22c55e" },
                { title: "GFC → Post-GFC Boom (2008–2013)", desc: "GFC crash -25% followed by the fastest recovery in history. Ultra-low rates + QE drove 2010 +18% and forced multiple cooling rounds.", color: "#60a5fa" },
                { title: "Cooling Cycle (2013–2016)", desc: "TDSR + ABSD finally worked after 3 rounds. 4-year bear market despite a healthy economy — proof that policy overrides fundamentals.", color: "#a78bfa" },
                { title: "Policy-Constrained Bull (2017–2023)", desc: "Gradual recovery then COVID surprise. 2020 defied consensus entirely; 2021–2022 were the hottest years since 2007.", color: "#fbbf24" },
                { title: "Deceleration Cycle (2024–)", desc: "Structurally slower growth as affordability bites. HDB upgrader demand is the backbone; foreign demand structurally suppressed.", color: "#94a3b8" },
              ].map(c => (
                <div key={c.title} style={{ ...styles.card, borderLeft: `3px solid ${c.color}` }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: c.color, marginBottom: 4 }}>{c.title}</div>
                  <div style={{ fontSize: 11, color: "#64748b", lineHeight: 1.6 }}>{c.desc}</div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* ── TAB: TABLE ── */}
        {tab === "table" && (
          <div style={{ ...styles.card, padding: 0, overflow: "hidden" }}>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                <thead>
                  <tr style={{ background: "#07111f", borderBottom: "1px solid #1e2d45" }}>
                    {["Year", "Regime", "Key Event", "Consensus", "Fcst Mid", "Actual", "Delta", "Verdict"].map((h, i) => (
                      <th key={h} style={{ padding: "10px 12px", textAlign: i >= 4 ? "center" : "left", fontSize: 9, letterSpacing: "1px", textTransform: "uppercase", color: "#334155", fontWeight: 700, whiteSpace: "nowrap" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.map((row, i) => {
                    return (
                      <tr key={row.year} className="trow"
                        onClick={() => { setSelectedYear(row.year); setTab("chart"); }}
                        style={{ borderBottom: "1px solid #0d1826", background: i % 2 === 0 ? "#0a1423" : "#060c18", transition: "background 0.12s" }}>
                        <td style={{ padding: "9px 12px", fontFamily: "'IBM Plex Mono'", fontWeight: 700, color: "#f1f5f9", fontSize: 12 }}>{row.year}</td>
                        <td style={{ padding: "9px 12px" }}>
                          <span style={styles.pill(REGIME_COLOR[row.regime])}>
                            <div style={{ width: 5, height: 5, borderRadius: "50%", background: REGIME_COLOR[row.regime] }} />
                            {row.regime}
                          </span>
                        </td>
                        <td style={{ padding: "9px 12px", color: "#64748b", maxWidth: 180 }}>{row.event}</td>
                        <td style={{ padding: "9px 12px", color: "#334155", fontSize: 10, maxWidth: 180 }}>
                          {row.consensus 
                            ? <span>{row.consensus.startsWith("[R]") 
                                ? <><span style={{ color: "#fbbf24", fontSize: 9 }}>[R] </span>{row.consensus.replace("[R] ", "")}</>
                                : row.consensus}
                              </span>
                            : "—"}
                        </td>
                        <td style={{ padding: "9px 12px", textAlign: "center", fontFamily: "'IBM Plex Mono'", color: "#3b82f6" }}>
                          {`${row.forecastMid > 0 ? "+" : ""}${row.forecastMid}%`}
                        </td>
                        <td style={{ padding: "9px 12px", textAlign: "center", fontFamily: "'IBM Plex Mono'", fontWeight: 700, fontSize: 13, color: row.actual >= 0 ? "#fbbf24" : "#f87171" }}>
                          {row.actual > 0 ? "+" : ""}{row.actual}%
                        </td>
                        <td style={{ padding: "9px 12px", textAlign: "center", fontFamily: "'IBM Plex Mono'", color: (row.actual - row.forecastMid) > 1 ? "#22c55e" : (row.actual - row.forecastMid) < -1 ? "#f87171" : "#94a3b8" }}>
                          {`${(row.actual - row.forecastMid) > 0 ? "+" : ""}${(row.actual - row.forecastMid).toFixed(1)}pp`}
                        </td>
                        <td style={{ padding: "9px 12px", textAlign: "center" }}>
                          <span style={{ ...styles.pill(MISS_COLOR[row.miss]), fontSize: 10 }}>{row.miss}</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── TAB: REGIME SIGNALS ── */}
        {tab === "signals" && (
          <>
            <div style={{ ...styles.card, marginBottom: 16, borderLeft: "3px solid #3b82f6" }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#60a5fa", marginBottom: 8 }}>How to detect regime shifts in Singapore property</div>
              <div style={{ fontSize: 12, color: "#64748b", lineHeight: 1.7 }}>
                Singapore's property market is policy-constrained, meaning classical momentum/mean-reversion models are regularly interrupted by exogenous government interventions.
                Regime shifts here have <strong style={{ color: "#94a3b8" }}>two flavours</strong>: (1) <strong style={{ color: "#22c55e" }}>demand-led shifts</strong> driven by macro/rates/sentiment that analysts typically miss,
                and (2) <strong style={{ color: "#a78bfa" }}>policy-induced shifts</strong> that are partially telegraphed but whose magnitude is uncertain.
                The 8 signals below form a composite scorecard — when 4+ signals are flashing in the same direction, a regime shift within 2–4 quarters is historically likely.
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12, marginBottom: 20 }}>
              {REGIME_SIGNALS.map((s, i) => (
                <div key={i} className="signal-card"
                  style={{ ...styles.card, cursor: "pointer", borderColor: signalOpen === i ? "#3b82f655" : "#1e2d45" }}
                  onClick={() => setSignalOpen(signalOpen === i ? null : i)}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                      <span style={{ fontSize: 20 }}>{s.icon}</span>
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: "#e2e8f0" }}>{s.name}</div>
                        <span style={{
                          fontSize: 9, padding: "1px 7px", borderRadius: 10, fontWeight: 700,
                          background: s.weight === "High" ? "#22c55e20" : s.weight === "Medium" ? "#fbbf2420" : "#94a3b820",
                          color: s.weight === "High" ? "#22c55e" : s.weight === "Medium" ? "#fbbf24" : "#94a3b8",
                          border: `1px solid ${s.weight === "High" ? "#22c55e44" : s.weight === "Medium" ? "#fbbf2444" : "#94a3b844"}`,
                        }}>
                          {s.weight} weight
                        </span>
                      </div>
                    </div>
                    <div style={{ color: "#334155", fontSize: 14 }}>{signalOpen === i ? "▲" : "▼"}</div>
                  </div>
                  {signalOpen === i && (
                    <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #1e2d45" }}>
                      <div style={{ fontSize: 12, color: "#94a3b8", lineHeight: 1.7, marginBottom: 8 }}>{s.description}</div>
                      <div style={{ fontSize: 11, color: "#475569" }}>
                        <span style={{ color: "#3b82f6" }}>Historical examples: </span>{s.examples}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Current signal scorecard */}
            <div style={{ ...styles.card, borderLeft: "3px solid #fbbf24" }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#fbbf24", marginBottom: 12 }}>Current Signal Scorecard (as of early 2026)</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8 }}>
                {[
                  { signal: "Interest Rate Inflection", reading: "Bullish", note: "SORA at ~1.2% and falling toward 1% mid-2026; stimulative for demand", direction: "up" },
                  { signal: "Policy Intervention Risk", reading: "Cautious", note: "Record 9 consecutive years of gains; government on watch if growth > 5%/yr", direction: "neutral" },
                  { signal: "Transaction Velocity", reading: "Bullish", note: "2025 new home sales >10,000 — highest since 2021; strong pent-up demand", direction: "up" },
                  { signal: "Developer Land Bids", reading: "Bullish", note: "Aggressive GLS bids in 2024-25 support future price floors", direction: "up" },
                  { signal: "HDB/Private Gap", reading: "Cautious", note: "Gap narrowing; HDB resale at record, reducing upgrader headroom", direction: "neutral" },
                  { signal: "Foreign Capital Flows", reading: "Muted", note: "60% ABSD structurally suppresses foreign demand; no near-term change", direction: "down" },
                  { signal: "Mortgage Credit", reading: "Bullish", note: "Housing loans +17% YoY in H1 2025; credit expansion supports demand", direction: "up" },
                  { signal: "Supply Pipeline", reading: "Bullish", note: "Thin 2025-26 completions (~5-7K units vs 20K normal) tightens resale supply", direction: "up" },
                ].map(s => {
                  const col = s.direction === "up" ? "#22c55e" : s.direction === "down" ? "#f87171" : "#fbbf24";
                  const arrow = s.direction === "up" ? "↑" : s.direction === "down" ? "↓" : "→";
                  return (
                    <div key={s.signal} style={{ background: "#07111f", border: `1px solid ${col}22`, borderRadius: 8, padding: "10px 14px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                        <div style={{ fontSize: 11, fontWeight: 600, color: "#94a3b8" }}>{s.signal}</div>
                        <span style={{ ...styles.pill(col), fontSize: 11 }}>{arrow} {s.reading}</span>
                      </div>
                      <div style={{ fontSize: 10, color: "#475569", lineHeight: 1.5 }}>{s.note}</div>
                    </div>
                  );
                })}
              </div>
              <div style={{ marginTop: 14, padding: "10px 14px", background: "#07111f", borderRadius: 8, borderLeft: "3px solid #22c55e" }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: "#22c55e", marginBottom: 4 }}>Composite Signal: Moderately Bullish (5/8 positive)</div>
                <div style={{ fontSize: 11, color: "#64748b", lineHeight: 1.6 }}>
                  The rate environment, thin supply pipeline, and strong volumes all point to continued price support in 2026. The two key risks are (1) a surprise policy intervention if prices accelerate past ~5% annually,
                  and (2) a macro shock from tariffs/trade war dampening employment. Base case aligns with 3–4% consensus — but upside surprise is more likely than downside, consistent with the historical record.
                </div>
              </div>
            </div>
          </>
        )}

        <div style={{ marginTop: 20, padding: "10px 16px", background: "#0a1423", border: "1px solid #1e2d45", borderRadius: 8, fontSize: 10, color: "#475569", lineHeight: 1.6 }}>
          <span style={{ color: "#fbbf24", fontWeight: 600 }}>Data note: </span>
          2015–2025 forecasts are published consensus ranges from CBRE, Knight Frank, DBS Research, PropNex, OrangeTee/Realion, ERA. &nbsp;
          1998–2014 forecasts marked [R] are <em>reconstructed estimates</em> derived from contemporaneous analyst commentary, DTZ/JLL/Knight Frank/CBRE annual outlook reports, and media coverage — they represent the documented market view at the time but should not be treated as verbatim published ranges.
          URA PPI actuals: Urban Redevelopment Authority (2009-Q1 = 100 base).
        </div>
      </div>
    </div>
  );
}