---
id: PLAT-WEB-FIREBASE
type: guide
layer: platforms
platform: [web]
architecture: web-spa
requires: [ARCH-WEB, PLAT-WEB-REACT, PLAT-WEB-STATE]
related: [PLAT-WEB-DEPLOY]
tags: [firebase, firestore, auth, on-snapshot, hooks, environment-variables, real-time]
---

# Firebase Integration Guide

*(Dashboard projects only — skip for static websites)*

Extends: `ARCH-WEB`

## Initialisation

Firebase is initialised once in `src/firebase/firebaseConfig.ts`. This file
exports the `firestore` and `auth` instances used across all hooks.

```typescript
// src/firebase/firebaseConfig.ts
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';

const app = initializeApp({
  apiKey:            import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain:        import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId:         import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket:     import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId:             import.meta.env.VITE_FIREBASE_APP_ID,
});

export const firestore = getFirestore(app);
export const auth      = getAuth(app);
```

**Rule PLAT-WEB-FB-CONFIG-01 (hard):** ALL Firebase config values MUST come from
`import.meta.env.VITE_*` environment variables. No API key, project ID, or any
other Firebase credential may be hardcoded in source files.

**Rule PLAT-WEB-FB-CONFIG-02 (hard):** `.env` and `.env.production` MUST be in
`.gitignore`. Commit a `.env.example` with placeholder values so contributors
know which variables are needed.

## Firestore data fetching

**Rule PLAT-WEB-FB-HOOKS-01 (hard):** Components MUST NOT call Firestore directly.
All Firestore interactions live in custom hooks in `src/hooks/`. Components call
hooks; hooks call Firestore.

**Rule PLAT-WEB-FB-SNAPSHOT-01 (soft):** Use `onSnapshot` for live data, not
`getDocs`. Dashboards display real-time data. One-shot `getDocs` is appropriate
only for write confirmations or admin operations where a stale read is acceptable.

```typescript
// src/hooks/useItems.ts
import { collection, onSnapshot, query, orderBy } from 'firebase/firestore';
import { firestore } from '../firebase/firebaseConfig';
import type { ItemDoc } from '../types/firestore';

export const useItems = () => {
  const [items,   setItems]   = useState<ItemDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    const q = query(collection(firestore, 'items'), orderBy('createdAt', 'desc'));
    const unsub = onSnapshot(
      q,
      snap => {
        setItems(snap.docs.map(d => ({ id: d.id, ...d.data() } as ItemDoc)));
        setLoading(false);
      },
      err => {
        setError(err.message);
        setLoading(false);
      },
    );
    return unsub;
  }, []);

  return { items, loading, error };
};
```

**Rule PLAT-WEB-FB-CLEANUP-01 (hard):** Every `onSnapshot` subscription MUST be
cleaned up by returning the unsubscribe function from `useEffect`. Failing to
clean up creates a memory leak and stale listeners that update state on an
unmounted component.

## Firestore types

**Rule PLAT-WEB-FB-TYPES-01 (hard):** Every Firestore collection MUST have a
corresponding TypeScript interface in `src/types/firestore.ts`. Document types
MUST NOT be defined inline inside hooks or components.

```typescript
// src/types/firestore.ts
export interface UserDoc {
  id: string;
  email: string;
  displayName: string;
  createdAt: string;
  isPremium: boolean;
}

export interface ContentDoc {
  id: string;
  title: string;
  subject: string;
  createdAt: string;
}
```

Cast documents explicitly when mapping snapshot results:

```typescript
snap.docs.map(d => ({ id: d.id, ...d.data() } as UserDoc))
```

## Auth

**Rule PLAT-WEB-FB-AUTH-01 (hard):** Auth state MUST be owned by a single
`AuthContext`. All components read auth state via the `useAuth()` hook. Never
call `onAuthStateChanged` directly in a component — doing so creates multiple
concurrent listeners and breaks on unmount.

```typescript
// Login
const handleLogin = async (email: string, password: string) => {
  try {
    await signInWithEmailAndPassword(auth, email, password);
    navigate('/');
  } catch {
    // show error feedback
  }
};

// Logout
const handleLogout = async () => {
  await signOut(auth);
  navigate('/login');
};
```

## Multi-environment config

Use `.env` for local development and `.env.production` for production builds.
Vite automatically picks up `.env.production` during `npm run build`.

```bash
# .env.example (committed)
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
```
