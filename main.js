// ── set colour────────────────────────────────────────────────────────────────────
const BUCKETS = [
  { label: '>95%',   min: 95,  max: 200, color: '#08519C' },
  { label: '90–95%', min: 90,  max: 95,  color: '#3182BD' },
  { label: '80–90%', min: 80,  max: 90,  color: '#6BAED6' },
  { label: '70–80%', min: 70,  max: 80,  color: '#9ECAE1' },
  { label: '60–70%', min: 60,  max: 70,  color: '#C6DBEF' },
  { label: '<60%',   min: 0,   max: 60,  color: '#D55E00' },
];

// Alpha-3 → ISO numeric
const A3_TO_NUM = {
  AFG:4,ALB:8,DZA:12,AGO:24,ARG:32,ARM:51,AUS:36,AZE:31,BGD:50,
  BLR:112,BEN:204,BTN:64,BOL:68,BIH:70,BWA:72,BRA:76,BFA:854,BDI:108,
  CPV:132,KHM:116,CMR:120,CAF:140,TCD:148,CHL:152,CHN:156,COL:170,
  COM:174,COD:180,COG:178,CRI:188,CIV:384,HRV:191,CUB:192,CYP:196,
  CZE:203,DNK:208,DJI:262,DOM:214,ECU:218,EGY:818,SLV:222,GNQ:226,
  ERI:232,ETH:231,FJI:242,FIN:246,FRA:250,GAB:266,GMB:270,GEO:268,
  DEU:276,GHA:288,GRC:300,GTM:320,GIN:324,GNB:624,GUY:328,HTI:332,
  HND:340,HUN:348,IND:356,IDN:360,IRN:364,IRQ:368,IRL:372,ISR:376,
  ITA:380,JAM:388,JPN:392,JOR:400,KAZ:398,KEN:404,PRK:408,KOR:410,
  KWT:414,KGZ:417,LAO:418,LBN:422,LSO:426,LBR:430,LBY:434,LTU:440,
  MKD:807,MDG:450,MWI:454,MYS:458,MDV:462,MLI:466,MRT:478,MEX:484,
  MDA:498,MNG:496,MNE:499,MAR:504,MOZ:508,MMR:104,NAM:516,NPL:524,
  NLD:528,NZL:554,NIC:558,NER:562,NGA:566,NOR:578,OMN:512,PAK:586,
  PAN:591,PNG:598,PRY:600,PER:604,PHL:608,POL:616,PRT:620,QAT:634,
  ROU:642,RUS:643,RWA:646,SAU:682,SEN:686,SLE:694,SOM:706,ZAF:710,
  SSD:728,ESP:724,LKA:144,SDN:729,SWZ:748,SWE:752,CHE:756,SYR:760,
  TJK:762,TZA:834,THA:764,TLS:626,TGO:768,TTO:780,TUN:788,TUR:792,
  TKM:795,UGA:800,UKR:804,ARE:784,GBR:826,USA:840,URY:858,UZB:860,
  VEN:862,VNM:704,YEM:887,ZMB:894,ZWE:716,SVK:703,SVN:705,BGR:100,
  EST:233,LVA:428,BLZ:84,SRB:688,BRB:52,GRD:308,VCT:670,ATG:28,
  COM:174,MDV:462,TLS:626,STP:678,WSM:882,TON:776,VUT:548,KIR:296,
  MHL:584,FSM:583,PLW:585,NRU:520,TUV:798,COK:184,NIU:570,
};

const NUM_TO_A3 = {};
Object.entries(A3_TO_NUM).forEach(([a3, num]) => {
  NUM_TO_A3[String(num)] = a3;
});

const W = 800, H = 400;

// ── initilise─────────────────────────────────────────────────────────────────────
let allData        = [];
let worldTopo      = null;
let currentYear    = 1999;
let playing        = false;
let playTimer      = null;
let activeContinent = 'all';
let selectedCountryId = null;
let activeBucket   = null;

// Pre-built lookup: year
const dataIndex = {};

function buildIndex(data) {
  data.forEach(r => {
    if (!dataIndex[r.year]) dataIndex[r.year] = {};
    dataIndex[r.year][r.id] = r;
  });
}

function getRecord(alpha3, year) {
  return (dataIndex[year] || {})[alpha3] || null;
}

// ── colour────────────────────────────────────────────────────────────────────
function colorFor(val) {
  if (val == null || isNaN(val)) return null;
  const b = BUCKETS.find(b => val >= b.min && val < b.max);
  return b ? b.color : null;
}

function bucketFor(val) {
  if (val == null || isNaN(val)) return null;
  return BUCKETS.find(b => val >= b.min && val < b.max) || null;
}

// ── map map ────────────────────────────────────────────────────────────
function drawMaps() {
  const features = topojson.feature(worldTopo, worldTopo.objects.countries).features;

  ['enrollment','completion'].forEach(field => {
    const svgId  = field === 'enrollment' ? 'svg-enrollment' : 'svg-completion';
    const svg    = d3.select('#' + svgId);

    const proj = d3.geoNaturalEarth1().scale(140).translate([W/2, H/2 + 15]);
    const path = d3.geoPath().projection(proj);

    // Hatch pattern
    let defs = svg.select('defs');
    if (defs.empty()) defs = svg.append('defs');
    if (defs.select('#hatch-' + field).empty()) {
      const pat = defs.append('pattern')
        .attr('id', 'hatch-' + field)
        .attr('patternUnits','userSpaceOnUse')
        .attr('width', 5).attr('height', 5)
        .attr('patternTransform','rotate(45)');
      pat.append('rect').attr('width',5).attr('height',5).attr('fill','#EBEBEB');
      pat.append('line').attr('x1',0).attr('y1',0).attr('x2',0).attr('y2',5)
        .attr('stroke','#BDBDBD').attr('stroke-width',1);
    }

    svg.selectAll('.country')
      .data(features, d => d.id)
      .join('path')
        .attr('class','country')
        .attr('d', path)

        // HOVER — shows tooltip only
        .on('mouseover', function(event, d) {
          const a3  = NUM_TO_A3[String(d.id)];
          const rec = a3 ? getRecord(a3, currentYear) : null;
          showTooltip(event, a3, rec);
        })
        .on('mousemove', moveTooltip)
        .on('mouseout', function() {
          hideTooltip();
        })

        // click to focus on the country
        .on('click', function(event, d) {
          const alreadySelected = (selectedCountryId === d.id);
          if (alreadySelected) {
            selectedCountryId = null;
            d3.selectAll('.country')
              .classed('country-selected', false)
              .classed('country-faded', false);
          } else {
            selectedCountryId = d.id;
            d3.selectAll('.country')
              .classed('country-selected', cd => cd.id === d.id)
              .classed('country-faded',    cd => cd.id !== d.id);
          }
        });

    updateMapColors(svgId, field);
  });
}

function updateMapColors(svgId, field) {
  const svg = d3.select('#' + svgId);
  svg.selectAll('.country').each(function(d) {
    const a3  = NUM_TO_A3[String(d.id)];
    const rec = a3 ? getRecord(a3, currentYear) : null;

    let fill   = 'url(#hatch-' + field + ')';
    let opacity = 1;

    if (rec && rec[field] != null) {
      fill = colorFor(rec[field]) || fill;
    }

    // Continent filter
    if (activeContinent !== 'all') {
      if (!rec || rec.continent !== activeContinent) {
        opacity = 0.1;
      }
    }

    // Bucket filter
    if (activeBucket !== null) {
      const b = rec ? bucketFor(rec[field]) : null;
      if (!b || b.label !== BUCKETS[activeBucket].label) {
        opacity = 0.1;
      }
    }

    d3.select(this)
      .attr('fill', fill)
      .attr('opacity', opacity);
  });
}

function updateBothColors() {
  updateMapColors('svg-enrollment', 'enrollment');
  updateMapColors('svg-completion', 'completion');
}

// ── update year ───────────────────────────────────────────────────────────────
function update(year) {
  currentYear = +year;
  document.getElementById('year-label').textContent = currentYear;
  document.getElementById('year-slider').value = currentYear;
  updateBothColors();
  updateStats();
}

// ── statics─────────────────────────────────────────────────────────────────────
function updateStats() {
  const yearRecs = Object.values(dataIndex[currentYear] || {});
  const visible  = activeContinent === 'all'
    ? yearRecs
    : yearRecs.filter(r => r.continent === activeContinent);
  const valid = visible.filter(r => r.enrollment != null && r.completion != null);

  document.getElementById('stat-countries').textContent = valid.length;
  document.getElementById('stat-enrol').textContent =
    valid.length ? d3.mean(valid, r => r.enrollment).toFixed(1) + '%' : '—';
  document.getElementById('stat-comp').textContent =
    valid.length ? d3.mean(valid, r => r.completion).toFixed(1) + '%' : '—';
  document.getElementById('stat-gap').textContent =
    valid.length ? d3.mean(valid, r => r.gap).toFixed(1) + ' pts' : '—';
}

// ── tooltip ───────────────────────────────────────────────────────────────────
const tooltip = document.getElementById('tooltip');

function showTooltip(event, a3, rec) {
  if (!rec && !a3) { hideTooltip(); return; }

  const countryName = rec ? rec.country : (a3 || 'Unknown');
  const sparkSVG    = rec ? buildSparkline(a3) : '';

  tooltip.innerHTML = `
    <div class="tt-country">${countryName}</div>
    <div class="tt-row">
      <span class="tt-label">Year</span>
      <span class="tt-val">${currentYear}</span>
    </div>
    <div class="tt-row">
      <span class="tt-label">Enrollment</span>
      <span class="tt-val">${rec && rec.enrollment != null ? rec.enrollment + '%' : '—'}</span>
    </div>
    <div class="tt-row">
      <span class="tt-label">Completion</span>
      <span class="tt-val">${rec && rec.completion != null ? rec.completion + '%' : '—'}</span>
    </div>
    <div class="tt-row">
      <span class="tt-label">Gap</span>
      <span class="tt-gap">${rec && rec.gap != null ? rec.gap + ' pts' : '—'}</span>
    </div>
    <div class="tt-row">
      <span class="tt-label">IWI (wealth)</span>
      <span class="tt-val">${rec && rec.iwi != null ? rec.iwi : '—'}</span>
    </div>
    ${sparkSVG ? `<div class="tt-spark">
      <div class="tt-spark-label">Gap trend 1999–2023</div>
      ${sparkSVG}
    </div>` : ''}
  `;
  tooltip.style.display = 'block';
  moveTooltip(event);
}

function moveTooltip(event) {
  const TT_W  = 274;  
  const TT_H  = 300; 
  const GAP   = 14;  
  const mx    = event.clientX;
  const my    = event.clientY;
  const vw    = window.innerWidth;
  const vh    = window.innerHeight;

  // Flip left 
  const left = (mx + GAP + TT_W > vw)
    ? mx - TT_W - GAP         
    : mx + GAP;                 

  // Flip up 
  const top = (my + GAP + TT_H > vh)
    ? my - TT_H                 
    : my + GAP;                

  tooltip.style.left = Math.max(4, left) + 'px';
  tooltip.style.top  = Math.max(4, top)  + 'px';
}

function hideTooltip() {
  tooltip.style.display = 'none';
}

function buildSparkline(a3) {
  const sparkData = allData
    .filter(r => r.id === a3 && r.gap != null)
    .sort((a, b) => a.year - b.year);
  if (sparkData.length < 2) return '';

  const ml = 32, mr = 12, mt = 8, mb = 24;
  const sw = 220, sh = 90;
  const iw = sw - ml - mr;
  const ih = sh - mt - mb;

  const minYear = d3.min(sparkData, d => d.year);
  const maxYear = d3.max(sparkData, d => d.year);
  const maxGap  = Math.min(60, Math.ceil(d3.max(sparkData, d => d.gap) / 10) * 10 + 5);

  const xS = d3.scaleLinear().domain([minYear, maxYear]).range([0, iw]);
  const yS = d3.scaleLinear().domain([0, maxGap]).range([ih, 0]);

  // Line path
  const lineFn = d3.line()
    .x(d => xS(d.year))
    .y(d => yS(d.gap))
    .curve(d3.curveMonotoneX);

  // Area fill path
  const areaFn = d3.area()
    .x(d => xS(d.year))
    .y0(ih)
    .y1(d => yS(d.gap))
    .curve(d3.curveMonotoneX);

  // Current year marker
  const currRec = sparkData.find(d => d.year === currentYear);
  const lastRec = sparkData[sparkData.length - 1];

  // Y axis ticks
  const yTicks = [0, Math.round(maxGap / 2), maxGap];

  // X axis ticks 
  const midYear = Math.round((minYear + maxYear) / 2);
  const xTicks  = [minYear, midYear, maxYear];

  let currentMarker = '';
  if (currRec) {
    const cx = xS(currRec.year);
    const cy = yS(currRec.gap);
    currentMarker = `
      <line x1="${cx}" y1="0" x2="${cx}" y2="${ih}"
        stroke="#08519C" stroke-width="1" stroke-dasharray="3,2" opacity="0.6"/>
      <circle cx="${cx}" cy="${cy}" r="4" fill="#08519C" stroke="#fff" stroke-width="1.5"/>
      <text x="${cx + 5}" y="${cy - 5}" font-size="9" fill="#08519C" font-weight="600">
        ${currRec.gap}pts
      </text>`;
  }

  const endCircle = `
    <circle cx="${xS(lastRec.year)}" cy="${yS(lastRec.gap)}"
      r="3.5" fill="#D55E00" stroke="#fff" stroke-width="1.5"/>`;

  const yAxisLines = yTicks.map(v =>
    `<line x1="0" y1="${yS(v)}" x2="${iw}" y2="${yS(v)}"
       stroke="#eee" stroke-width="1"/>`
  ).join('');

  const yAxisLabels = yTicks.map(v =>
    `<text x="-4" y="${yS(v)}" font-size="8.5" fill="#aaa"
       text-anchor="end" dominant-baseline="middle">${v}</text>`
  ).join('');

  const xAxisLabels = xTicks.map(y =>
    `<text x="${xS(y)}" y="${ih + 14}" font-size="8.5" fill="#aaa"
       text-anchor="middle">${y}</text>`
  ).join('');

  return `
  <svg width="${sw}" height="${sh}"
       style="display:block;overflow:visible;margin-top:4px">
    <defs>
      <linearGradient id="sparkGrad-${a3}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"   stop-color="#D55E00" stop-opacity="0.25"/>
        <stop offset="100%" stop-color="#D55E00" stop-opacity="0.02"/>
      </linearGradient>
    </defs>
    <g transform="translate(${ml},${mt})">
      ${yAxisLines}
      <path d="${areaFn(sparkData)}"
        fill="url(#sparkGrad-${a3})"/>
      <path d="${lineFn(sparkData)}"
        fill="none" stroke="#D55E00" stroke-width="2" stroke-linecap="round"/>
      ${endCircle}
      ${currentMarker}
      ${yAxisLabels}
      ${xAxisLabels}
      <text x="-${ml - 2}" y="${ih / 2}"
        font-size="8" fill="#bbb" text-anchor="middle"
        transform="rotate(-90,-${ml - 2},${ih / 2})">Gap %</text>
      <line x1="0" y1="0" x2="0" y2="${ih}"
        stroke="#ddd" stroke-width="1"/>
      <line x1="0" y1="${ih}" x2="${iw}" y2="${ih}"
        stroke="#ddd" stroke-width="1"/>
    </g>
  </svg>`;
}

// ── filter ────────────────────────────────────────────────────────────────────
function buildLegend() {
  const container = document.getElementById('legend-buckets');
  container.innerHTML = '';
  BUCKETS.forEach((b, i) => {
    const el = document.createElement('div');
    el.className = 'legend-bucket';
    el.innerHTML = `<div class="legend-swatch"
      style="background:${b.color};width:14px;height:14px;border-radius:2px;flex-shrink:0"></div>
      <span>${b.label}</span>`;
    el.style.cssText = `display:flex;align-items:center;gap:4px;font-size:11px;
      color:#555;cursor:pointer;padding:2px 6px;border-radius:3px;
      border:1.5px solid transparent;transition:border-color 0.15s`;
    el.addEventListener('click', () => {
      activeBucket = activeBucket === i ? null : i;
      document.querySelectorAll('.legend-bucket')
        .forEach((e,j) => e.style.borderColor = j === activeBucket ? '#333' : 'transparent');
      updateBothColors();
    });
    container.appendChild(el);
  });
}

// ── play button ──────────────────────────────────────────────────────────────
function startPlay() {
  playing = true;
  document.getElementById('play-btn').textContent = '⏸ Pause';
  playTimer = setInterval(() => {
    const next = currentYear >= 2023 ? 1999 : currentYear + 1;
    update(next);
  }, 700);
}

function stopPlay() {
  playing = false;
  clearInterval(playTimer);
  document.getElementById('play-btn').innerHTML = '&#9654; Play';
}

// ── init ──────────────────────────────────────────────────────────────────────
Promise.all([
  d3.json('data/data.json'),
  d3.json('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json')
]).then(([data, world]) => {
  allData   = data;
  worldTopo = world;

  buildIndex(data);
  buildLegend();
  drawMaps();
  update(1999);

  document.getElementById('year-slider').addEventListener('input', e => {
    stopPlay();
    update(+e.target.value);
  });

  document.getElementById('play-btn').addEventListener('click', () => {
    playing ? stopPlay() : startPlay();
  });

  document.getElementById('continent-filter').addEventListener('change', e => {
    activeContinent = e.target.value;
    updateBothColors();
    updateStats();
  });

}).catch(err => {
  console.error('Error loading data:', err);
  document.body.innerHTML += `<div style="color:red;padding:20px;font-family:sans-serif">
    <b>Error:</b> ${err.message}<br><br>
    Make sure you are running from WebStorm's built-in server (not file://)
    and that <code>data/data.json</code> exists.
  </div>`;
});