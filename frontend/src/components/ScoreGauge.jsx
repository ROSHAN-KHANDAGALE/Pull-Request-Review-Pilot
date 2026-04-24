export default function ScoreGauge({ score }) {
  const pct = Math.min(100, Math.max(0, (score / 10000) * 100));

  const getColor = () => {
    if (pct >= 80) return "var(--score-high)";
    if (pct >= 50) return "var(--score-mid)";
    return "var(--score-low)";
  };

  const getLabel = () => {
    if (pct >= 80) return "Excellent";
    if (pct >= 60) return "Good";
    if (pct >= 40) return "Fair";
    return "Needs Work";
  };

  // SVG arc math
  const r = 54;
  const cx = 70;
  const cy = 70;
  const startAngle = -210;
  const endAngle = 30;
  const totalDeg = endAngle - startAngle;
  const filledDeg = (pct / 100) * totalDeg;

  const toRad = (deg) => (deg * Math.PI) / 180;
  const arcX = (deg) => cx + r * Math.cos(toRad(deg));
  const arcY = (deg) => cy + r * Math.sin(toRad(deg));

  const describeArc = (start, end) => {
    const s = { x: arcX(start), y: arcY(start) };
    const e = { x: arcX(end), y: arcY(end) };
    const large = end - start > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`;
  };

  return (
    <div className="score-gauge">
      <svg viewBox="0 0 140 100" width="180">
        {/* Track */}
        <path
          d={describeArc(startAngle, endAngle)}
          fill="none"
          stroke="var(--track)"
          strokeWidth="8"
          strokeLinecap="round"
        />
        {/* Fill */}
        <path
          d={describeArc(startAngle, startAngle + filledDeg)}
          fill="none"
          stroke={getColor()}
          strokeWidth="8"
          strokeLinecap="round"
          style={{ transition: "all 0.8s ease" }}
        />
      </svg>
      <div className="gauge-center">
        <span className="gauge-score" style={{ color: getColor() }}>
          {score.toLocaleString()}
        </span>
        <span className="gauge-label">{getLabel()}</span>
        <span className="gauge-max">/ 10,000</span>
      </div>
    </div>
  );
}
