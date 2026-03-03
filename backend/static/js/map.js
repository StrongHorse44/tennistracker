/**
 * CourtTracker — Leaflet Map Initialization
 */

function initMap(locations) {
  var map = L.map('map', {
    scrollWheelZoom: false
  }).setView([30, 0], 2);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(map);

  var surfaceColors = {
    'Hard': '#3b6fa0',
    'Clay': '#c4622d',
    'Grass': '#4a8c3f',
    'Carpet': '#7a5c8f'
  };

  var bounds = [];

  locations.forEach(function(loc) {
    var t = loc.tournament;
    if (!t.latitude || !t.longitude) return;

    var lat = t.latitude;
    var lng = t.longitude;
    bounds.push([lat, lng]);

    var color = surfaceColors[t.surface] || '#6c757d';

    var marker = L.circleMarker([lat, lng], {
      radius: Math.min(6 + (loc.players ? loc.players.length : 0), 16),
      fillColor: color,
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.85
    }).addTo(map);

    var playerCount = loc.players ? loc.players.length : loc.player_count || 0;
    var playerList = '';
    if (loc.players && loc.players.length > 0) {
      var shown = loc.players.slice(0, 8);
      shown.forEach(function(p) {
        var name = p.player.full_name;
        var rank = p.player.current_singles_rank ? '#' + p.player.current_singles_rank : '';
        playerList += '<div style="font-size:0.8rem">' + rank + ' ' + name + '</div>';
      });
      if (loc.players.length > 8) {
        playerList += '<div style="font-size:0.75rem;color:#888">+' + (loc.players.length - 8) + ' more</div>';
      }
    }

    var popup = '<div class="ct-map-popup">'
      + '<h6>' + t.name + '</h6>'
      + '<div style="margin-bottom:6px">'
      + '<span class="ct-surface ct-surface-' + (t.surface || '').toLowerCase() + '">' + (t.surface || '') + '</span> '
      + '<span style="font-size:0.8rem;color:#666">' + t.city + ', ' + (t.country_name || t.country) + '</span>'
      + '</div>'
      + '<div style="font-size:0.8rem;margin-bottom:4px"><strong>' + playerCount + ' player' + (playerCount !== 1 ? 's' : '') + '</strong></div>'
      + playerList
      + '</div>';

    marker.bindPopup(popup, { maxWidth: 280 });
  });

  if (bounds.length > 0) {
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 5 });
  }

  // Fix tile loading issue when map is in a hidden/resized container
  setTimeout(function() { map.invalidateSize(); }, 200);

  return map;
}
