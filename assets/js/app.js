const CHANNELS = {
  "BEIN Sports 1": "beee1", "BEIN Sports 2": "beee2", "BEIN Sports 3": "beee3",
  "BEIN Sports 4": "beee4", "BEIN Sports 5": "beee5", "BEIN Sports 6": "beee6",
  "BEIN MAX 1": "beemax1", "BEIN MAX 2": "beemax2", "BEIN MAX 3": "beemax3",
  "BEIN MAX 4": "beemax4", "BEIN MAX 5": "beemax5", "BEIN MAX 6": "beemax6"
};

let hls = null;
let selectedQuality = 'auto';

function getQualityButtons() {
  return Array.from(document.querySelectorAll('.q-pill'));
}

function setQualityButtonsEnabled(enabled) {
  getQualityButtons().forEach(btn => {
    btn.disabled = !enabled;
    btn.classList.toggle('is-disabled', !enabled);
  });
}

function selectQualityButton(mode) {
  getQualityButtons().forEach(btn => btn.classList.remove('active'));
  const btn = document.getElementById(`q-${mode}`);
  if (btn) btn.classList.add('active');
}

function getLevelForQuality(mode) {
  if (!hls || !hls.levels || hls.levels.length === 0) return -1;
  const levels = hls.levels
    .map((level, index) => ({ index, bitrate: level.bitrate || 0, height: level.height || 0 }))
    .sort((a, b) => (a.bitrate - b.bitrate) || (a.height - b.height));

  if (mode === 'low') return levels[0].index;
  if (mode === 'high') return levels[levels.length - 1].index;
  if (mode === 'medium') return levels[Math.floor((levels.length - 1) / 2)].index;
  return -1;
}

function formatQualityLabel(level) {
  if (!level) return '';
  if (level.height) return `${level.height}p`;
  if (level.bitrate) return `${Math.round(level.bitrate / 1000)}k`;
  return '';
}

function updateQualityLabels() {
  if (!hls || !hls.levels || hls.levels.length === 0) return;
  const low = hls.levels[getLevelForQuality('low')];
  const mid = hls.levels[getLevelForQuality('medium')];
  const high = hls.levels[getLevelForQuality('high')];
  document.getElementById('q-low').textContent = `توفير البيانات ${formatQualityLabel(low)}`.trim();
  document.getElementById('q-medium').textContent = `جودة متوسطة ${formatQualityLabel(mid)}`.trim();
  document.getElementById('q-high').textContent = `عالية HD ${formatQualityLabel(high)}`.trim();
}

function resetQualityLabels() {
  document.getElementById('q-low').textContent = 'توفير البيانات';
  document.getElementById('q-medium').textContent = 'جودة متوسطة';
  document.getElementById('q-high').textContent = 'عالية HD';
}

function applySelectedQuality() {
  if (!hls) return;
  const level = selectedQuality === 'auto' ? -1 : getLevelForQuality(selectedQuality);
  hls.currentLevel = level;
  hls.nextLevel = level;
  hls.loadLevel = level;
  selectQualityButton(selectedQuality);
}

function syncToLiveEdge(video) {
  if (!hls || !Number.isFinite(hls.liveSyncPosition)) return;
  const drift = hls.liveSyncPosition - video.currentTime;
  if (drift > 10) {
    video.currentTime = hls.liveSyncPosition;
  }
}

function toggleMenu() {
  document.getElementById('menuBtn').classList.toggle('open');
  document.getElementById('sidebarMenu').classList.toggle('active');
}

function switchSection(sect) {
  toggleMenu();
  document.querySelectorAll('.app-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  
  document.getElementById(`section-${sect}`).classList.add('active');
  document.getElementById(`nav-${sect}`).classList.add('active');
}

async function playChannel(name) {
  const badge = document.getElementById('statusBadge');
  document.getElementById('currentChannel').textContent = name;
  badge.innerHTML = "<span></span>⏳ جاري الاتصال...";
  badge.className = "live-indicator";
  selectedQuality = 'auto';
  selectQualityButton('auto');
  resetQualityLabels();
  setQualityButtonsEnabled(false);
  
  document.querySelectorAll('.channel-card').forEach(c => c.classList.toggle('active', c.dataset.id === name));

  try {
    const r = await fetch(`/api/channel?ch=${CHANNELS[name]}`);
    const data = await r.json();
    if(!data.ok || !data.stream_url) {
      badge.innerHTML = "<span></span>❌ القناة مغلقة حالياً"; return;
    }

    const video = document.getElementById('video');
    if (hls) hls.destroy();
    hls = null;

    const proxyUrl = `/api/proxy?url={url}`.replace('{url}', encodeURIComponent(data.stream_url));

    if (Hls.isSupported()) {
      hls = new Hls({
        maxBufferLength: 30,
maxMaxBufferLength: 60,
liveSyncDurationCount: 5,
liveMaxLatencyDurationCount: 10,
lowLatencyMode: false,
      });
      hls.loadSource(proxyUrl);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        badge.innerHTML = "<span></span>🟢 مباشر";
        badge.classList.add('streaming');
        if (hls.levels && hls.levels.length > 1) {
          updateQualityLabels();
          setQualityButtonsEnabled(true);
        } else {
          resetQualityLabels();
          setQualityButtonsEnabled(false);
        }
        applySelectedQuality();
        syncToLiveEdge(video);
        video.play().catch(()=>{});
      });
      hls.on(Hls.Events.ERROR, (event, data) => {
        if (!data || !data.fatal) return;
        if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
          badge.innerHTML = "<span></span>⏳ إعادة الاتصال...";
          hls.startLoad();
          return;
        }
        if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
          badge.innerHTML = "<span></span>⏳ إصلاح التشغيل...";
          hls.recoverMediaError();
          return;
        }
        badge.innerHTML = "<span></span>⚠️ تعذر تشغيل البث";
        setQualityButtonsEnabled(false);
        hls.destroy();
        hls = null;
      });
    } else {
      video.src = proxyUrl;
      setQualityButtonsEnabled(false);
    }
  } catch(e) {
    badge.innerHTML = "<span></span>⚠️ خطأ بالاتصال";
    setQualityButtonsEnabled(false);
  }
}

function changeQuality(mode, el) {
  selectedQuality = mode;
  selectQualityButton(mode);
  if (!hls || !hls.levels || hls.levels.length <= 1) return;
  applySelectedQuality();
}

function initDeviceInfo() {
  document.getElementById('dev-ua').textContent = navigator.userAgent.substring(0, 50) + "...";
  document.getElementById('dev-screen').textContent = `${window.screen.width} x ${window.screen.height} بكسل`;
  document.getElementById('dev-vendor').textContent = navigator.vendor || "محرك ويب مستقل";
  document.getElementById('dev-lang').textContent = navigator.language;
}

const grid = document.getElementById('channelsGrid');
Object.keys(CHANNELS).forEach(name => {
  const div = document.createElement('div');
  div.className = 'channel-card';
  div.dataset.id = name;
  div.innerHTML = `<strong style="font-size:15px; display:block; margin-bottom:4px;">📺 ${name.replace('BEIN Sports ', 'بين ').replace('BEIN MAX ', 'ماكس ')}</strong><span style="font-size:11px; color:var(--text-muted); font-weight:500;">جودة عالية مستقرة</span>`;
  div.onclick = () => playChannel(name);
  grid.appendChild(div);
});

initDeviceInfo();
resetQualityLabels();
setQualityButtonsEnabled(false);
