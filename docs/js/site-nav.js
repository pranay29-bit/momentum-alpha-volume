/* Shared site nav for the static pages (watchlist / position size / position tracker).
   Same links as the nav on the home page and the dated dashboards, so you can
   jump from any tool straight back to a dashboard.
   Needs js/latest.js to be loaded first (it sets window.MA_LATEST = "YYYY-MM-DD"). */
(function () {
  var host = document.getElementById('siteNav');
  if (!host) return;

  var latest = window.MA_LATEST || '';
  var slug = latest.replace(/-/g, '');
  var page = (location.pathname.split('/').pop() || 'index.html').toLowerCase();

  function dash(file) { return latest ? latest + '/' + file + '_' + slug + '.html' : 'index.html'; }

  var links = [
    { href: 'index.html',                      cls: 'navy',   label: '🏠 Home' },
    { href: dash('dashboard'),                 cls: 'indigo', label: '📊 Momentum' },
    { href: dash('elite_dashboard'),           cls: 'green',  label: '⚡ Elite' },
    { href: dash('volume_dashboard'),          cls: 'blue',   label: '🔵 Volume' },
    { href: dash('rocket_dashboard'),          cls: 'amber',  label: '🚀 Rocket' },
    { href: dash('newrshigh_dashboard'),       cls: 'rose',   label: '🔥 New RS High' },
    { href: dash('stage4_dashboard'),          cls: 'red',    label: '📉 Stage 4' },
    { href: dash('sme_momentum_dashboard'),    cls: 'violet', label: '🏷️ SME Momentum' },
    { href: dash('sme_elite_dashboard'),       cls: 'violet', label: '🏷️ SME Elite' },
    { href: 'watchlist.html',                  cls: 'gold',   label: '⭐ Watchlist' },
    { href: 'position-size.html',              cls: 'violet', label: '📐 Position Size' },
    { href: 'position-tracker.html',           cls: 'navy',   label: '📈 Position Tracker' }
  ];

  host.innerHTML = links.map(function (l) {
    var active = l.href.toLowerCase() === page ? ' is-active' : '';
    return '<a href="' + l.href + '" class="btn-link ' + l.cls + active + '">' + l.label + '</a>';
  }).join('');
})();
