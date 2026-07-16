const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('fs');
const path = require('path');
const { getProvider } = require('./providers');
const { MihomoManager } = require('./core/manager');
const { prepareRuntimeConfig } = require('./core/config');
const { getSystemProxy, setSystemProxy } = require('./system-proxy');
const { createTray } = require('./tray');
require('./providers/builtin');

const settings = JSON.parse(fs.readFileSync(path.join(__dirname, 'settings.json'), 'utf8'));
const core = new MihomoManager(settings);

async function loadSubscription() {
  const source = settings.subscription;
  const text = await getProvider(source.provider).load(source);
  const config = prepareRuntimeConfig(text, core.configPath);
  core.start();
  return {
    proxies: Array.isArray(config.proxies) ? config.proxies : [],
    groups: Array.isArray(config['proxy-groups']) ? config['proxy-groups'] : [],
    updatedAt: new Date().toISOString(),
  };
}

async function coreRequest(route, options = {}) {
  const headers = {};
  if (settings.mihomoSecret) headers.Authorization = `Bearer ${settings.mihomoSecret}`;
  const response = await fetch(`${settings.mihomoApi}${route}`, { ...options, headers });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  const text = await response.text();
  return text ? JSON.parse(text) : {};
}

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1120,
    height: 720,
    minWidth: 860,
    minHeight: 560,
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false },
  });
  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  return mainWindow;
}

ipcMain.handle('subscription:load', loadSubscription);
ipcMain.handle('core:status', () => coreRequest('/'));
ipcMain.handle('core:proxies', () => coreRequest('/proxies'));
ipcMain.handle('core:select', (_event, group, proxy) => coreRequest(`/proxies/${encodeURIComponent(group)}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: proxy }),
}));
ipcMain.handle('system-proxy:get', getSystemProxy);
ipcMain.handle('system-proxy:set', (_event, enabled) => setSystemProxy(Boolean(enabled)));

let tray;

app.whenReady().then(async () => {
  core.start();
  mainWindow = createWindow();
  tray = await createTray(mainWindow, getSystemProxy, setSystemProxy, () => app.quit());
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});
app.on('before-quit', () => core.stop());
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
