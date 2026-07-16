const { Menu, Tray, nativeImage } = require('electron');

const ICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><rect width="16" height="16" rx="3" fill="#43b38a"/><path d="M4 4h8v2H6v4h5v2H4z" fill="#102018"/></svg>';

async function createTray(window, getProxy, setProxy, quit) {
  const icon = nativeImage.createFromDataURL(`data:image/svg+xml;base64,${Buffer.from(ICON_SVG).toString('base64')}`);
  const tray = new Tray(icon);
  tray.setToolTip('CATVPN');
  const checked = await getProxy().catch(() => false);
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: '打开 CATVPN', click: () => { window.show(); window.focus(); } },
    { type: 'separator' },
    { label: '系统代理', type: 'checkbox', checked, click: (item) => setProxy(item.checked).catch(() => { item.checked = !item.checked; }) },
    { type: 'separator' },
    { label: '退出', click: quit },
  ]));
  tray.on('double-click', () => { window.show(); window.focus(); });
  return tray;
}

module.exports = { createTray };
