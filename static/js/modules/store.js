const stores = {};

export const Store = {
    create: function(name, initialState = {}, cachePattern = null) {
        if (stores[name]) {
            console.warn(`Store "${name}" already exists`);
            return stores[name];
        }

        let state = { ...initialState };
        const listeners = [];

        const store = {
            name: name,

            getState: function() {
                return { ...state };
            },

            setState: function(newState) {
                const prev = { ...state };
                state = { ...state, ...newState };
                if (cachePattern && window.clearApiCache) {
                    window.clearApiCache(cachePattern);
                }
                listeners.forEach(listener => {
                    try {
                        listener(state, prev);
                    } catch (e) {
                        console.error(`Store "${name}" listener error:`, e);
                    }
                });
            },

            subscribe: function(listener) {
                listeners.push(listener);
                return () => {
                    const index = listeners.indexOf(listener);
                    if (index > -1) listeners.splice(index, 1);
                };
            },

            destroy: function() {
                delete stores[name];
                listeners.length = 0;
            }
        };

        stores[name] = store;
        return store;
    },

    get: function(name) {
        return stores[name] || null;
    }
};