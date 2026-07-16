const providers = new Map();

function registerProvider(name, provider) {
  if (!name || !provider || typeof provider.load !== 'function') throw new Error(`Invalid provider: ${name}`);
  providers.set(name, provider);
}

function getProvider(name) {
  const provider = providers.get(name);
  if (!provider) throw new Error(`Provider not found: ${name}`);
  return provider;
}

module.exports = { registerProvider, getProvider };
