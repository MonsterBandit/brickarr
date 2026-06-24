import { create } from 'zustand';

interface AuthState {
  apiKey: string | null;
  sessionUser: string | null;
  setApiKey: (key: string | null) => void;
  setUser: (user: string | null) => void;
  clear: () => void;
}

const KEY_STORAGE = 'brickarr.apiKey';
const USER_STORAGE = 'brickarr.user';

export const useAuth = create<AuthState>((set) => ({
  apiKey: typeof localStorage !== 'undefined' ? localStorage.getItem(KEY_STORAGE) : null,
  sessionUser: typeof localStorage !== 'undefined' ? localStorage.getItem(USER_STORAGE) : null,
  setApiKey: (key) => {
    if (key) localStorage.setItem(KEY_STORAGE, key);
    else localStorage.removeItem(KEY_STORAGE);
    set({ apiKey: key });
  },
  setUser: (user) => {
    if (user) localStorage.setItem(USER_STORAGE, user);
    else localStorage.removeItem(USER_STORAGE);
    set({ sessionUser: user });
  },
  clear: () => {
    localStorage.removeItem(KEY_STORAGE);
    localStorage.removeItem(USER_STORAGE);
    set({ apiKey: null, sessionUser: null });
  },
}));
