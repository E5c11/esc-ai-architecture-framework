---
id: PLAT-WEB-STATE
type: guide
layer: platforms
platform: [web]
architecture: web-spa
requires: [ARCH-WEB, ARCH-WEB-COMPONENTS]
related: [PLAT-WEB-REACT, PLAT-WEB-FIREBASE]
tags: [state, use-state, custom-hooks, context, react-router, routing, auth-guard]
---

# State Management and Routing

Extends: `ARCH-WEB`, `ARCH-WEB-COMPONENTS`

## State management tiers

Use the simplest tier that solves the problem. Add complexity only when a simpler
tier genuinely cannot support the requirement.

### Tier 1: `useState` — local, isolated state

Default for all component-local state: form inputs, toggles, UI mode switches.

```typescript
const [value, setValue]     = useState<string>('');
const [loading, setLoading] = useState(false);
const [isOpen, setIsOpen]   = useState(false);
```

### Tier 2: Custom hook — reusable or side-effect-bearing logic

Use a custom hook when the same data-fetching or side-effect logic is needed
in more than one component, or when the logic is complex enough to warrant its
own file.

```rule
id: PLAT-WEB-STATE-HOOK-01
statement: Every data-fetching hook MUST return the three-field shape `{ data, loading, error }`.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-STATE-HOOK-01 — Every data-fetching hook MUST return the three-field shape `{ data, loading, error }`.
```

The consumer (container component) guards all three states before rendering. Never return only `data` without `loading` and `error` — the container cannot safely guard without them.

```typescript
// src/hooks/useItems.ts
export const useItems = (): { items: Item[]; loading: boolean; error: string | null } => {
  const [items,   setItems]   = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    // fetch or subscribe...
    return cleanup;
  }, []);

  return { items, loading, error };
};
```

```rule
id: PLAT-WEB-STATE-HOOK-02
statement: Custom hooks MUST live in `src/hooks/`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-STATE-HOOK-02 — Custom hooks MUST live in `src/hooks/`.
```

Data-fetching logic MUST NOT be embedded inside component function bodies. Components call hooks; hooks own the fetching logic.

### Tier 3: React Context — global or cross-tree shared state

Use Context for state that must be accessible across the entire component tree
without prop drilling: authentication state, theme selection, user preferences.

```typescript
// src/contexts/AuthContext.tsx
interface AuthContextValue {
  user: User | null;
  loading: boolean;
}

const AuthContext = createContext<AuthContextValue>({ user: null, loading: true });

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser]       = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    return onAuthStateChanged(auth, u => {
      setUser(u);
      setLoading(false);
    });
  }, []);

  return <AuthContext.Provider value={{ user, loading }}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
```

```rule
id: PLAT-WEB-STATE-CTX-01
statement: Do not use Redux or Zustand unless the project grows beyond what Context + hooks can reasonably handle.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-STATE-CTX-01 — Do not use Redux or Zustand unless the project grows beyond what Context + hooks can reasonably handle.
```

Global state managers add serialisation and devtool overhead that is not justified for dashboard or website scale.

```rule
id: PLAT-WEB-STATE-CTX-02
statement: Auth state MUST be owned by `AuthContext`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-STATE-CTX-02 — Auth state MUST be owned by `AuthContext`.
```

All components that need the current user call `useAuth()`. Never call `onAuthStateChanged` directly inside a component — it creates multiple listeners and the subscription is not cleaned up on unmount.

## Routing

Use `react-router-dom` v6+. Route structure lives in `App.tsx`.

### Website routing

```tsx
<BrowserRouter>
  <Routes>
    <Route path="/"        element={<Home />} />
    <Route path="/about"   element={<About />} />
    <Route path="*"        element={<Navigate to="/" replace />} />
  </Routes>
</BrowserRouter>
```

Always include a catch-all `path="*"` that redirects to the home route.

### Dashboard routing — protected routes

```tsx
<BrowserRouter>
  <Routes>
    <Route path="/login" element={<LoginScreen />} />
    <Route element={<AuthGuard />}>
      <Route element={<AppShell />}>
        <Route path="/"         element={<OverviewPage />} />
        <Route path="/users"    element={<UsersPage />} />
        <Route path="/content"  element={<ContentPage />} />
      </Route>
    </Route>
  </Routes>
</BrowserRouter>
```

```rule
id: PLAT-WEB-ROUTE-GUARD-01
statement: Every protected route MUST be wrapped in an `AuthGuard`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-ROUTE-GUARD-01 — Every protected route MUST be wrapped in an `AuthGuard`.
```

The guard reads auth state from `AuthContext` and redirects to the login route if the user is unauthenticated.

```typescript
// src/auth/AuthGuard.tsx
const AuthGuard: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) return <LoadingSpinner />;
  if (!user)   return <Navigate to="/login" replace />;

  return <Outlet />;
};
```

The guard handles the loading state explicitly — never render the protected content
while auth state is still resolving.

### Active route detection

```typescript
const location = useLocation();
const isActive = (path: string) =>
  location.pathname === path || location.pathname.startsWith(path + '/');
```

### SEO meta tags (websites only)

Use `react-helmet-async` with `HelmetProvider` at the root. Each page declares
its own `<title>` and `<meta name="description">`:

```tsx
// main.tsx — wrap the app
<HelmetProvider><App /></HelmetProvider>

// Home.tsx — set page-specific meta
<Helmet>
  <title>Page Title – Brand Name</title>
  <meta name="description" content="Page description for search engines." />
</Helmet>
```
