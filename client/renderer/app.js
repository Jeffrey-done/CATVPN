const state = { proxies: [], query: '' };
const $ = (id) => document.getElementById(id);

function showError(error) {
  $('notice').textContent = error.message || String(error);
  $('notice').classList.remove('hidden');
}

function render() {
  const query = state.query.toLowerCase();
  const visible = state.proxies.filter((proxy) => JSON.stringify(proxy).toLowerCase().includes(query));
  $('node-count').textContent = state.proxies.length;
  $('nodes').innerHTML = visible.map((proxy) => `
    <tr><td class="node-name">${proxy.name || '未命名'}</td><td>${proxy.server || '--'}:${proxy.port || '--'}</td><td><span class="tag">${proxy.type || '--'}</span></td><td class="latency">${proxy['catvpn-latency'] ? `${proxy['catvpn-latency']} ms` : '--'}</td><td><button class="select" data-name="${encodeURIComponent(proxy.name || '')}">选择</button></td></tr>
  `).join('') || '<tr><td colspan="5" class="empty">暂无节点，请刷新订阅</td></tr>';
  document.querySelectorAll('.select').forEach((button) => button.addEventListener('click', async () => {
    try { await window.catvpn.selectProxy('PROXY', decodeURIComponent(button.dataset.name)); } catch (error) { showError(error); }
  }));
}

async function refresh() {
  $('refresh').disabled = true;
  $('refresh').textContent = '更新中...';
  $('notice').classList.add('hidden');
  try {
    const result = await window.catvpn.loadSubscription();
    state.proxies = result.proxies;
    try {
      const live = await window.catvpn.coreProxies();
      const liveNodes = live.proxies || {};
      state.proxies = state.proxies.map((proxy) => ({ ...proxy, 'catvpn-latency': liveNodes[proxy.name]?.history?.at(-1)?.delay }));
    } catch (_) {}
    $('updated-at').textContent = new Date(result.updatedAt).toLocaleTimeString();
    render();
  } catch (error) { showError(error); }
  finally { $('refresh').disabled = false; $('refresh').textContent = '刷新订阅'; }
}

$('refresh').addEventListener('click', refresh);
$('search').addEventListener('input', (event) => { state.query = event.target.value; render(); });
window.catvpn.getSystemProxy().then((enabled) => {
  const button = $('proxy-toggle');
  button.dataset.enabled = enabled ? 'true' : 'false';
  button.textContent = enabled ? '系统代理：已开启' : '系统代理：已关闭';
  button.classList.toggle('enabled', enabled);
}).catch(() => { $('proxy-toggle').textContent = '系统代理：不可用'; });
$('proxy-toggle').addEventListener('click', async () => {
  const enabled = $('proxy-toggle').dataset.enabled === 'true';
  try {
    const next = await window.catvpn.setSystemProxy(!enabled);
    $('proxy-toggle').dataset.enabled = String(next);
    $('proxy-toggle').textContent = next ? '系统代理：已开启' : '系统代理：已关闭';
    $('proxy-toggle').classList.toggle('enabled', next);
  } catch (error) { showError(error); }
});
window.catvpn.coreStatus().then((info) => { if (info.version) $('core-status').textContent = `Mihomo ${info.version}`; }).catch(() => {});
refresh();
