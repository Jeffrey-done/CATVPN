const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('catvpn', {
  loadSubscription: () => ipcRenderer.invoke('subscription:load'),
  coreStatus: () => ipcRenderer.invoke('core:status'),
  coreProxies: () => ipcRenderer.invoke('core:proxies'),
  selectProxy: (group, proxy) => ipcRenderer.invoke('core:select', group, proxy),
  getSystemProxy: () => ipcRenderer.invoke('system-proxy:get'),
  setSystemProxy: (enabled) => ipcRenderer.invoke('system-proxy:set', enabled),
});
