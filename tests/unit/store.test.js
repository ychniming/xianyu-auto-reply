import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Store } from '../../static/js/modules/store.js';

describe('Store', () => {
    beforeEach(() => {
        Store.get('test')?.destroy();
    });

    afterEach(() => {
        Store.get('test')?.destroy();
    });

    describe('create', () => {
        it('should create a new store with initial state', () => {
            const store = Store.create('test', { count: 0, name: 'test' });
            expect(store).toBeDefined();
            expect(store.name).toBe('test');

            const state = store.getState();
            expect(state.count).toBe(0);
            expect(state.name).toBe('test');
        });

        it('should return existing store if name already exists', () => {
            const store1 = Store.create('test', { value: 1 });
            const store2 = Store.create('test', { value: 2 });

            expect(store1).toBe(store2);
            expect(store2.getState().value).toBe(1);
        });

        it('should allow independent stores with same initial state', () => {
            const store1 = Store.create('test1', { count: 0 });
            const store2 = Store.create('test2', { count: 0 });

            store1.setState({ count: 5 });

            expect(store1.getState().count).toBe(5);
            expect(store2.getState().count).toBe(0);
        });
    });

    describe('getState', () => {
        it('should return a copy of state', () => {
            const store = Store.create('test', { items: [1, 2, 3] });
            const state1 = store.getState();
            const state2 = store.getState();

            expect(state1).not.toBe(state2);
            expect(state1).toEqual(state2);
        });

        it('should not allow direct state mutation', () => {
            const store = Store.create('test', { count: 0 });
            const state = store.getState();

            state.count = 999;

            expect(store.getState().count).toBe(0);
        });
    });

    describe('setState', () => {
        it('should update state with new values', () => {
            const store = Store.create('test', { count: 0, name: 'old' });

            store.setState({ count: 10 });

            expect(store.getState().count).toBe(10);
            expect(store.getState().name).toBe('old');
        });

        it('should replace entire state when new object is set', () => {
            const store = Store.create('test', { a: 1, b: 2 });

            store.setState({ c: 3 });

            const state = store.getState();
            expect(state.a).toBeUndefined();
            expect(state.b).toBeUndefined();
            expect(state.c).toBe(3);
        });

        it('should notify all listeners on state change', () => {
            const store = Store.create('test', { value: 0 });
            const listener1 = vi.fn();
            const listener2 = vi.fn();

            store.subscribe(listener1);
            store.subscribe(listener2);

            store.setState({ value: 5 });

            expect(listener1).toHaveBeenCalledTimes(1);
            expect(listener2).toHaveBeenCalledTimes(1);
            expect(listener1).toHaveBeenCalledWith(
                { value: 5 },
                { value: 0 }
            );
        });

        it('should handle listener errors gracefully', () => {
            const store = Store.create('test', { value: 0 });
            const errorListener = vi.fn(() => {
                throw new Error('Listener error');
            });
            const normalListener = vi.fn();

            store.subscribe(errorListener);
            store.subscribe(normalListener);

            store.setState({ value: 5 });

            expect(errorListener).toHaveBeenCalled();
            expect(normalListener).toHaveBeenCalled();
        });
    });

    describe('subscribe', () => {
        it('should call listener immediately with current state', () => {
            const store = Store.create('test', { count: 0 });
            const listener = vi.fn();

            store.subscribe(listener);

            expect(listener).toHaveBeenCalledWith({ count: 0 }, { count: 0 });
        });

        it('should return unsubscribe function', () => {
            const store = Store.create('test', { value: 0 });
            const listener = vi.fn();

            const unsubscribe = store.subscribe(listener);
            unsubscribe();

            store.setState({ value: 5 });

            expect(listener).toHaveBeenCalledTimes(1);
        });

        it('should handle multiple subscriptions', () => {
            const store = Store.create('test', { value: 0 });
            const listeners = [vi.fn(), vi.fn(), vi.fn()];

            listeners.forEach(l => store.subscribe(l));

            store.setState({ value: 1 });

            listeners.forEach(l => expect(l).toHaveBeenCalledTimes(1));
        });
    });

    describe('destroy', () => {
        it('should remove store and clear listeners', () => {
            const store = Store.create('test', { value: 0 });
            store.subscribe(vi.fn());

            store.destroy();

            expect(Store.get('test')).toBeNull();
            store.setState({ value: 5 });
        });

        it('should handle destroying non-existent store', () => {
            expect(() => Store.get('nonexistent')?.destroy()).not.toThrow();
        });
    });

    describe('get', () => {
        it('should return store by name', () => {
            const store = Store.create('test', { value: 0 });

            expect(Store.get('test')).toBe(store);
        });

        it('should return null for non-existent store', () => {
            expect(Store.get('nonexistent')).toBeNull();
        });
    });
});