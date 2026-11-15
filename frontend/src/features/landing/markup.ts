// Landing page markup (ported from the mockup). Links with data-link are routed inside the app.
export const LANDING_MARKUP = `

<nav id="nav" class="glass top" aria-label="Main">
  <a class="logo" href="#top"><i><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"><path d="M12 3v6M12 15v6M3 12h6M15 12h6"/><circle cx="12" cy="12" r="2.2" fill="#fff" stroke="none"/></svg></i>RescueForce</a>
  <div class="navlinks"><a href="#problem">Problem</a><a href="#how">How it works</a><a href="#see">What you see</a><a href="#agents">AI agents</a><a href="#evidence">Evidence</a><a href="#data">Data</a></div>
  <a class="btn primary" href="/map" data-link aria-label="Try RescueForce"><span>Try RescueForce</span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
</nav>

<!-- ================= HERO: scroll story ================= -->
<header id="hero">
  <div class="stage" id="top">
    <canvas id="globe" aria-hidden="true"></canvas>

    <div class="bird" id="bird" aria-hidden="true">
      <div class="plane" id="plane">
        <svg viewBox="0 0 1600 1270" id="overlay"></svg>
        <div class="hires" id="hires"><svg id="hov"></svg></div>
      </div>
    </div>
    <div class="shade" id="shade"></div>
    <canvas id="fire" aria-hidden="true"></canvas>
    <div id="fx" aria-hidden="true"></div>
    <div class="vignette"></div>

    <div class="textfade" id="tfade"></div>
    <div class="hero-copy" id="copy">
      <span class="kicker">NASA Space Apps 2026 · Dancing with the SARs challenge</span>
      <h1><span class="line"><span>War damages more</span></span><span class="line"><span>than buildings.</span></span><span class="line"><span>It disrupts <em>people's lives.</em></span></span></h1>
      <p>We help identify damaged areas, affected communities and available services to support faster emergency response and recovery.</p>
      <div class="hero-cta">
        <a class="btn primary" href="/map" data-link>Try RescueForce <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
        <a class="btn" href="#how">How it works</a>
      </div>
    </div>
    <div class="scrollhint" id="hint"><i></i>Scroll to explore</div>

    <div class="caption" id="cap1"><span class="kicker">From orbit to street level</span><h2>Satellites see change <em>no one has reported yet.</em></h2></div>
    <div class="caption" id="cap2"><span class="kicker">Sample incidents</span><h2>RescueForce ranks <em>where help is needed first.</em></h2></div>
    <div class="caption" id="capZ"><span class="kicker">Close-up · sample incident</span><h2>Damaged buildings, a fire, <em>and the ways in.</em></h2></div>

    <!-- plain-language dashboard cards; they arrive by themselves while you scroll -->
    <div class="cards-layer" id="cards">
      <div class="ccol">
        <div class="fcard glass mob-hide" id="fc-rank">
          <div class="k"><i><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 20V10M12 20V4M19 20v-7"/></svg></i>Where to help first</div>
          <div class="prio"><span class="n" style="--c:var(--dmg-severe)">1</span><div><b>Khiam east</b><small>Most people and damage</small><div class="bar"><i style="width:92%"></i></div></div></div>
          <div class="prio"><span class="n" style="--c:var(--dmg-destroyed)">2</span><div><b>Bint Jbeil centre</b><small>Heavy damage, one satellite so far</small><div class="bar"><i style="width:76%"></i></div></div></div>
          <div class="prio"><span class="n" style="--c:var(--dmg-moderate)">3</span><div><b>Aitaroun south</b><small>Reported by residents</small><div class="bar"><i style="width:58%"></i></div></div></div>
        </div>
        <div class="fcard glass mob-hide" id="fc-fire">
          <div class="k"><i><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22c4 0 7-2.8 7-6.8 0-3.6-2.6-5.7-4-8.2-.6 2-1.6 3-3 3.6.4-3.2-1-6.4-3.6-8.6C8.3 6 5 8.6 5 14.6 5 19 8 22 12 22z"/></svg></i>Fire seen from space</div>
          <p><b>2 hot spots</b> found by NASA satellites tonight, accurate to about 375 m.</p>
          <div class="row"><span class="chip ev-o">Observed</span></div>
        </div>
        <div class="fcard glass mob-hide" id="fc-route">
          <div class="k"><i><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 3 5 21M16 3l3 18M12 4v3M12 10v4M12 17v3"/></svg></i>Ways in</div>
          <div class="route-row"><svg width="24" height="10"><path d="M1 5h22" stroke="#f1f4f3" stroke-width="3.5"/></svg><b>Western road</b><span>open on the map, not yet checked</span></div>
          <div class="route-row"><svg width="24" height="10"><path d="M1 5h22" stroke="#ff5a5f" stroke-width="3.5" stroke-dasharray="5 3"/></svg><b>Ridge road</b><span>may be blocked by damage</span></div>
        </div>
      </div>
      <div class="ccol mid">
        <div class="caption cap-mid" id="cap3"><span class="kicker">One screen for responders</span><h2>Everything in one place. <em>The officer decides.</em></h2></div>
        <div class="fcard glass note mob-hide" id="fc-pass">
          <div class="k" style="justify-content:center"><i><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg></i>Latest satellite pass · 14 Nov</div>
          <div class="passbar"><span class="on"></span><span class="on"></span><span></span><span class="on"></span><span class="on"></span></div>
          <p style="margin-top:7px">New building changes show within 72 hours of each pass.</p>
        </div>
      </div>
      <div class="ccol">
        <div class="fcard glass" id="fc-inc">
          <div class="k"><i><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg></i>Priority 1 · Khiam east</div>
          <h4><span class="hatch" style="--c:var(--dmg-severe)"></span>&nbsp; Heavy damage likely</h4>
          <p>About <b>1,800–2,900 people</b> live nearby. <b>14–22 buildings</b> may be damaged.</p>
          <div class="row"><span class="chip ev-c">Confirmed by 2 satellites</span></div>
        </div>
        <div class="fcard glass mob-hide" id="fc-power">
          <div class="k"><i><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M13 2 5 14h6l-1 8 8-12h-6z"/></svg></i>Lights went out</div>
          <p>Night-time lights dropped here: <b>possible power loss</b> for <b>900–2,100 people</b>.</p>
          <div class="row"><span class="tag pw">Not yet confirmed on the ground</span></div>
        </div>
        <div class="fcard glass" id="fc-shelter">
          <div class="k"><i><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/></svg></i>Nearest shelter option</div>
          <h4>Sample shelter 1</h4>
          <p><b>1.8 km by road</b> · room for about <b>250–400 people</b></p>
          <div class="row"><span class="tag">Candidate · check before use</span></div>
        </div>
      </div>
    </div>
  </div>
</header>

<!-- ================= 01 PROBLEM ================= -->
<section class="block" id="problem">
  <div class="wrap">
    <div class="num-kicker reveal"><b>01</b><span></span><span class="kicker">The problem</span></div>
    <h2 class="title reveal">In a crisis, the picture arrives <em>late and in pieces.</em></h2>
    <p class="lead reveal">Damage reports, fire alerts, power cuts and road closures live in different places. RescueForce brings scattered information together so responders can understand the impact and see where support is needed.</p>
    <div class="pains">
      <div class="pain glass reveal"><div class="ico"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg></div><h3>Slow to see</h3><p>Ground reports can take days, and some areas are too risky to reach at all.</p></div>
      <div class="pain glass reveal"><div class="ico"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="3" y="4" width="7" height="7" rx="2"/><rect x="14" y="4" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></svg></div><h3>Scattered data</h3><p>Damage, fires, night lights, population and roads sit in separate tools and files.</p></div>
      <div class="pain glass reveal"><div class="ico"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg></div><h3>Hard to trust</h3><p>A rumour and a satellite observation often look the same on a map.</p></div>
    </div>
  </div>
</section>

<!-- ================= 02 HOW IT WORKS ================= -->
<section class="block" id="how">
  <div class="wrap">
    <div class="num-kicker reveal"><b>02</b><span></span><span class="kicker">How it works</span></div>
    <h2 class="title reveal">From satellite data <em>to better decisions.</em></h2>
    <div class="flow">
      <div class="pulse" id="pulse"></div>
      <div class="fstep reveal"><div class="dot"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M4 16 16 4l4 4-12 12z"/><path d="m9 11 4 4M3 21l3-3"/><path d="M17 13a6 6 0 0 1-6 6"/></svg></div><span class="n">Step 1</span><h3>Satellites detect</h3><p>Radar, night-light and thermal satellites spot possible changes on the ground, day or night, through cloud.</p></div>
      <div class="fstep reveal"><div class="dot"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="8" r="2.5"/><circle cx="10" cy="18" r="2.5"/><path d="m8 7.5 7.6 0M7 8.2l2 7.4M16.4 10l-4.8 6.3"/></svg></div><span class="n">Step 2</span><h3>RescueForce analyses</h3><p>Its AI agents connect the evidence, rank the impact on people and services, and suggest next checks and routes.</p></div>
      <div class="fstep reveal"><div class="dot"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/><path d="m15.5 17.5 2 2 3.5-3.5"/></svg></div><span class="n">Step 3</span><h3>Responders decide</h3><p>Officers review the findings, check them on the ground and make the call. Suggestions never act on their own.</p></div>
    </div>
  </div>
</section>

<!-- ================= 03 WHAT YOU SEE ================= -->
<section class="block" id="see">
  <div class="wrap">
    <div class="num-kicker reveal"><b>03</b><span></span><span class="kicker">What you can see</span></div>
    <h2 class="title reveal">Everything important, <em>in one place.</em></h2>
    <div class="cards">
      <article class="scard glass reveal"><div class="shot" data-bbox="35.6145,33.3255,35.6255,33.3345"><svg viewBox="0 0 400 300"><defs><pattern id="h1" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="2.5" height="7" fill="#f5904f"/></pattern><pattern id="h2" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="2.5" height="7" fill="#ff7a93"/></pattern></defs><rect x="150" y="105" width="46" height="40" fill="url(#h1)" stroke="#f5904f" stroke-width="2"/><rect x="214" y="132" width="40" height="36" fill="url(#h2)" stroke="#ff7a93" stroke-width="2"/><rect x="120" y="170" width="34" height="30" fill="url(#h1)" stroke="#eadf73" stroke-width="2"/><circle cx="173" cy="125" r="34" fill="none" stroke="#45c79c" stroke-width="2" stroke-dasharray="5 4"/></svg><span class="lbl chip ev-c">Corroborated</span></div>
        <div class="body"><h3>Damage candidates</h3><p>Potentially damaged buildings and areas, hatched by class and never shown as confirmed.</p></div></article>
      <article class="scard glass reveal"><div class="shot" data-bbox="35.6165,33.3265,35.6255,33.334"><svg viewBox="0 0 400 300"><defs><radialGradient id="fg"><stop offset="0" stop-color="#fff2c8"/><stop offset=".3" stop-color="#ffa050" stop-opacity=".9"/><stop offset="1" stop-color="#ff5a1e" stop-opacity="0"/></radialGradient></defs><circle cx="210" cy="150" r="118" fill="none" stroke="#ff8a4d" stroke-width="2" stroke-dasharray="8 5"/><circle cx="210" cy="150" r="40" fill="url(#fg)"><animate attributeName="r" values="36;44;38;42;36" dur="1.6s" repeatCount="indefinite"/></circle><circle cx="262" cy="118" r="26" fill="url(#fg)"><animate attributeName="r" values="24;30;25;28;24" dur="1.3s" repeatCount="indefinite"/></circle></svg><span class="lbl chip ev-o">Observed</span></div>
        <div class="body"><h3>Fire detections</h3><p>Satellite-detected fires with their 375 m uncertainty ring, updated through the day.</p></div></article>
      <article class="scard glass reveal"><div class="shot" data-bbox="35.595,33.315,35.645,33.345"><svg viewBox="0 0 400 300"><defs><pattern id="pw" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="3" fill="#9d93e6" fill-opacity=".55"/><rect y="3" width="8" height="5" fill="#04050a" fill-opacity=".5"/></pattern></defs><rect x="60" y="60" width="120" height="110" fill="url(#pw)" stroke="#9d93e6" stroke-dasharray="6 4" stroke-width="1.6"/><rect x="190" y="120" width="120" height="110" fill="url(#pw)" stroke="#9d93e6" stroke-dasharray="6 4" stroke-width="1.6"/><rect x="250" y="20" width="110" height="90" fill="#f3e3a1" fill-opacity=".14"/></svg><span class="lbl chip ev-c">2 satellites agree</span></div>
        <div class="body"><h3>Possible power loss</h3><p>Unusual drops in night-time lights, with the people and facilities inside each dark area.</p></div></article>
      <article class="scard glass reveal"><div class="shot" data-bbox="35.600,33.322,35.630,33.344"><svg viewBox="0 0 400 300"><path d="M30 40 C90 70 120 110 170 140 S 250 190 300 210" fill="none" stroke="#0a0d0f" stroke-opacity=".6" stroke-width="11" stroke-linecap="round"/><path d="M30 40 C90 70 120 110 170 140 S 250 190 300 210" fill="none" stroke="#f1f4f3" stroke-width="5" stroke-linecap="round" class="draw"/><path d="M170 140 C 210 130 250 110 330 100" fill="none" stroke="#ff5a5f" stroke-width="5" stroke-dasharray="12 7" stroke-linecap="round"/><g transform="translate(300 210)"><rect x="-16" y="-16" width="32" height="32" rx="9" fill="rgba(14,18,21,.92)" stroke="#f1f4f3" stroke-width="2" stroke-dasharray="4 3"/><path d="M-8 2 0-6 8 2M-6 0v8h12V0" fill="none" stroke="#f1f4f3" stroke-width="2"/></g></svg><span class="lbl tag" style="background:rgba(10,13,15,.8)">Not verified</span></div>
        <div class="body"><h3>Routes &amp; candidate shelters</h3><p>Routes on real roads and mapped shelter sites, with roads near damage flagged as possibly blocked.</p></div></article>
    </div>
  </div>
</section>

<!-- ================= 04 AI AGENTS ================= -->
<section class="block" id="agents">
  <div class="wrap">
    <div class="num-kicker reveal"><b>04</b><span></span><span class="kicker">AI agents</span></div>
    <h2 class="title reveal">AI that suggests. <em>People decide.</em></h2>
    <p class="lead reveal">Four small agents read the satellite evidence and turn it into plain answers. They explain their reasons, show what is still unknown, and never act on their own.</p>
    <div class="agents">
      <div class="agent glass reveal"><div class="ico"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M5 20V10M12 20V4M19 20v-7"/></svg></div>
        <h3>Ranking agent</h3><p>Orders incidents by people affected, damage, fires, power loss and how fresh the data is.</p>
        <div class="eg">“<b>Khiam east first</b>: most people nearby and two satellites agree.”</div></div>
      <div class="agent glass reveal"><div class="ico"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg></div>
        <h3>Insights agent</h3><p>Writes 3–5 short findings for each incident, each with its evidence label and source date.</p>
        <div class="eg">“Radar change runs along the eastern ridge road.” <b>Observed</b></div></div>
      <div class="agent glass reveal"><div class="ico"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 6h10M4 12h16M4 18h7"/><circle cx="17" cy="6" r="2"/><circle cx="14" cy="18" r="2"/></svg></div>
        <h3>Decision assistant</h3><p>Suggests next checks, route options and nearby shelter sites. Every idea is marked unverified.</p>
        <div class="eg">“Ask a field team to check the ridge road <b>before routing vehicles</b>.”</div></div>
      <div class="agent glass reveal"><div class="ico"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 3v18M17 7.5c0-1.9-2.2-3-5-3s-5 1.1-5 3 2.2 2.6 5 3.2 5 1.4 5 3.3-2.2 3-5 3-5-1.1-5-3"/></svg></div>
        <h3>Rebuild budget</h3><p>Gives an indicative cost range for each area, with the assumptions listed.</p>
        <div class="eg">“<b>4.2–9.8 million USD</b> · indicative, not a quote.”</div></div>
    </div>
  </div>
</section>

<!-- ================= 04 EVIDENCE ================= -->
<section class="block" id="evidence">
  <div class="wrap">
    <div class="num-kicker reveal"><b>05</b><span></span><span class="kicker">Evidence you can trust</span></div>
    <h2 class="title reveal">Know what is observed, reported <em>and still uncertain.</em></h2>
    <div class="evgrid">
      <div class="ev glass reveal" style="--c:var(--ev-observed)"><span class="chip">Observed</span><h3>Seen by a sensor</h3><p>Detected through available satellite observations.</p></div>
      <div class="ev glass reveal" style="--c:var(--ev-reported)"><span class="chip">Reported</span><h3>Told by a source</h3><p>Shared by a field team, a municipality or the media.</p></div>
      <div class="ev glass reveal" style="--c:var(--ev-corroborated)"><span class="chip">Corroborated</span><h3>Backed twice</h3><p>Supported by more than one independent source.</p></div>
      <div class="ev glass reveal" style="--c:var(--ev-unknown)"><span class="chip">Unknown</span><h3>Not enough yet</h3><p>Too little evidence to say. RescueForce shows the gap instead of guessing.</p></div>
    </div>
    <div class="banner glass reveal"><b>Candidates, <em>not facts.</em></b><span>Every damage area, route and shelter is a candidate until someone checks it on the ground. Numbers are shown as ranges, and nothing is ever labelled safe.</span></div>
  </div>
</section>

<!-- ================= 05 DATA ================= -->
<section class="block" id="data">
  <div class="wrap">
    <div class="num-kicker reveal"><b>06</b><span></span><span class="kicker">Built on open data</span></div>
    <h2 class="title reveal">Trusted sources, <em>free and open.</em></h2>
    <div class="data">
      <div class="ds glass reveal"><span class="org">NASA · ISRO</span><b>NISAR</b><span>L-band radar change for damage candidates</span></div>
      <div class="ds glass reveal"><span class="org">ESA · NASA JPL</span><b>Sentinel-1 (OPERA RTC)</b><span>Second radar check on each candidate</span></div>
      <div class="ds glass reveal"><span class="org">NASA</span><b>Black Marble</b><span>Night lights for possible power loss</span></div>
      <div class="ds glass reveal"><span class="org">NASA</span><b>FIRMS (VIIRS)</b><span>Near-real-time fire detections</span></div>
      <div class="ds glass reveal"><span class="org">University of Southampton</span><b>WorldPop</b><span>People living in each area, as a range</span></div>
      <div class="ds glass reveal"><span class="org">OSM community</span><b>OpenStreetMap</b><span>Buildings, roads and facilities</span></div>
      <div class="ds glass reveal"><span class="org">EU JRC</span><b>GHSL</b><span>Building heights and floors</span></div>
      <div class="ds glass free reveal"><b>All free, <em style="font-style:italic;color:#ffb48a">all open.</em></b><span>No paid data, no private feeds.</span></div>
    </div>
  </div>
</section>


<!-- ================= TRY ================= -->
<section id="try">
  <div class="wrap">
    <div class="tryp glass reveal">
      <div>
        <span class="kicker">Try RescueForce</span>
        <h2 style="margin-top:16px">See the impact <em>the way responders will.</em></h2>
        <p>Open the interactive map with sample incidents: real terrain, 3D buildings, fires, routes and shelters. No account and no setup needed.</p>
        <ul><li>Cinematic 3D, 2D and split view</li><li>Ranking, insights and a decision assistant</li><li>Routes on real roads and candidate shelters</li></ul>
      </div>
      <div class="open glass">
        <div class="shot" data-bbox="35.6105,33.3255,35.6285,33.3365"><svg viewBox="0 0 400 240"><defs><pattern id="oh" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="2.5" height="7" fill="#f5904f"/></pattern><radialGradient id="og"><stop offset="0" stop-color="#fff2c8"/><stop offset=".3" stop-color="#ffa050" stop-opacity=".9"/><stop offset="1" stop-color="#ff5a1e" stop-opacity="0"/></radialGradient></defs>
          <path d="M20 40 C90 70 140 100 190 120" fill="none" stroke="#f1f4f3" stroke-width="4" stroke-linecap="round"/><path d="M190 140 C 240 135 290 120 370 112" fill="none" stroke="#ff5a5f" stroke-width="4" stroke-dasharray="10 6" stroke-linecap="round"/>
          <rect x="176" y="106" width="30" height="26" fill="url(#oh)" stroke="#f5904f" stroke-width="2"/><circle cx="214" cy="122" r="22" fill="url(#og)"><animate attributeName="r" values="20;26;21;24;20" dur="1.5s" repeatCount="indefinite"/></circle>
          <g transform="translate(60 60)"><rect x="-13" y="-13" width="26" height="26" rx="7" fill="rgba(14,18,21,.92)" stroke="#f1f4f3" stroke-width="2" stroke-dasharray="4 3"/><path d="M-7 2 0-5 7 2M-5 0v7h10V0" fill="none" stroke="#f1f4f3" stroke-width="2"/></g></svg>
          <span class="lbl chip ev-c">Live demo · sample data</span></div>
        <div class="open-body">
          <ul class="checks"><li>No account needed</li><li>Realistic sample incidents</li><li>Works on desktop and phone</li></ul>
          <a class="btn primary" href="/map" data-link>Open RescueForce <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
          <p class="hint2">Opens the interactive 3D map in this tab.</p>
        </div>
      </div>
    </div>
  </div>
</section>



<footer>
  <div class="wrap">
    <div class="foot-top">
      <div class="foot-brand">
        <a class="logo" href="#top"><i><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"><path d="M12 3v6M12 15v6M3 12h6M15 12h6"/><circle cx="12" cy="12" r="2.2" fill="#fff" stroke="none"/></svg></i>RescueForce</a>
        <p>Satellite-based insight for emergency responders: damaged areas, affected communities and available services, in one place.</p>
      </div>
      <div class="foot-col"><h5>Product</h5><ul><li><a href="#how">How it works</a></li><li><a href="#see">What you can see</a></li><li><a href="#agents">AI agents</a></li><li><a href="#evidence">Evidence labels</a></li><li><a href="/map" data-link>Live demo</a></li></ul></div>
      <div class="foot-col"><h5>Open data</h5><ul><li>NASA NISAR · Black Marble · FIRMS</li><li>ESA Sentinel-1 (OPERA RTC)</li><li>WorldPop · GHSL</li><li>© OpenStreetMap contributors</li><li>Imagery: Esri World Imagery</li></ul></div>
      <div class="foot-col"><h5>Project</h5><ul><li>NASA Space Apps Challenge 2026</li><li>Challenge: Dancing with the SARs</li><li><a href="https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars" target="_blank" rel="noopener">GitHub repository ↗</a></li><li><a href="#data">Data sources</a></li></ul></div>
    </div>
    <div class="principles"><span>Open data</span><span>No vehicle or phone tracking</span><span>Candidates, not facts</span><span>Ranges, never single numbers</span><span>People decide, AI suggests</span></div>
    <div class="foot-word" aria-hidden="true">RescueForce</div>
    <div class="foot-bottom"><span>© 2026 RescueForce team · Built for NASA Space Apps 2026</span><span>All incidents shown are sample data. Fire and smoke are illustrative effects.</span></div>
  </div>
</footer>

`
