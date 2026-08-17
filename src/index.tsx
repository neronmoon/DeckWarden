import {
  ButtonItem,
  Focusable,
  PanelSection,
  PanelSectionRow,
  TextField,
  staticClasses,
} from "@decky/ui";
import { definePlugin, toaster } from "@decky/api";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FaKey } from "react-icons/fa";
import {
  getPassword,
  getSetting,
  getUsername,
  listEntries,
  lock,
  login,
  logout,
  setSetting,
  status,
  sync,
  unlock,
  type Status,
  type VaultEntry,
} from "./api";
import { typeText } from "./typeText";

function LoginView({
  initialEmail,
  onUnlocked,
}: {
  initialEmail: string;
  onUnlocked: () => void;
}) {
  const [email, setEmail] = useState(initialEmail);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const onLogin = async () => {
    setBusy(true);
    setError("");
    const result = await login(email.trim(), password);
    setPassword("");
    setBusy(false);
    if (!result.ok) {
      setError(result.error || "Login failed");
      return;
    }
    onUnlocked();
  };

  return (
    <PanelSection title="Bitwarden Cloud">
      <PanelSectionRow>
        <TextField
          label="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </PanelSectionRow>
      <PanelSectionRow>
        <TextField
          label="Master password"
          bIsPassword
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          disabled={busy || !email.trim() || !password}
          onClick={onLogin}
        >
          {busy ? "Logging in…" : "Log in"}
        </ButtonItem>
      </PanelSectionRow>
      {error ? (
        <PanelSectionRow>
          <div>{error}</div>
        </PanelSectionRow>
      ) : null}
    </PanelSection>
  );
}

function UnlockView({
  email,
  onUnlocked,
  onLogout,
}: {
  email: string;
  onUnlocked: () => void;
  onLogout: () => void;
}) {
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const onUnlock = async () => {
    setBusy(true);
    setError("");
    const result = await unlock(password);
    setPassword("");
    setBusy(false);
    if (!result.ok) {
      setError(result.error || "Unlock failed");
      return;
    }
    onUnlocked();
  };

  return (
    <PanelSection title="Locked">
      {email ? (
        <PanelSectionRow>
          <div style={{ opacity: 0.8 }}>{email}</div>
        </PanelSectionRow>
      ) : null}
      <PanelSectionRow>
        <TextField
          label="Master password"
          bIsPassword
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem layout="below" disabled={busy || !password} onClick={onUnlock}>
          {busy ? "Unlocking…" : "Unlock"}
        </ButtonItem>
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem layout="below" disabled={busy} onClick={onLogout}>
          Log out
        </ButtonItem>
      </PanelSectionRow>
      {error ? (
        <PanelSectionRow>
          <div>{error}</div>
        </PanelSectionRow>
      ) : null}
    </PanelSection>
  );
}

function EntryRow({
  entry,
  revealed,
  onReveal,
}: {
  entry: VaultEntry;
  revealed: string | null;
  onReveal: (id: string, secret: string | null) => void;
}) {
  const typePassword = async () => {
    const secret = await getPassword(entry.id);
    if (!secret) {
      toaster.toast({ title: "DeckWarden", body: "No password" });
      return;
    }
    toaster.toast({ title: "DeckWarden", body: "Password typed" });
    await typeText(secret);
  };

  const typeUser = async () => {
    const user = await getUsername(entry.id);
    if (!user) {
      toaster.toast({ title: "DeckWarden", body: "No username" });
      return;
    }
    toaster.toast({ title: "DeckWarden", body: "Username typed" });
    await typeText(user);
  };

  const reveal = async () => {
    const secret = await getPassword(entry.id);
    onReveal(entry.id, secret || "(empty)");
    window.setTimeout(() => onReveal(entry.id, null), 5000);
  };

  return (
    <Focusable
      onActivate={typePassword}
      onOKActionDescription="Type password"
      onSecondaryButton={typeUser}
      onSecondaryActionDescription="Type username"
      onOptionsButton={reveal}
      onOptionsActionDescription="Reveal"
      style={{ padding: "8px 0" }}
    >
      <div style={{ fontWeight: 600 }}>{entry.name}</div>
      <div style={{ opacity: 0.7, fontSize: "0.85em" }}>{entry.user || "—"}</div>
      {revealed !== null ? (
        <div style={{ marginTop: 4, wordBreak: "break-all" }}>{revealed}</div>
      ) : null}
    </Focusable>
  );
}

function SearchView({ onLocked }: { onLocked: () => void }) {
  const [query, setQuery] = useState("");
  const [entries, setEntries] = useState<VaultEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [revealed, setRevealed] = useState<Record<string, string>>({});
  const saveTimer = useRef<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const [list, last] = await Promise.all([
      listEntries(),
      getSetting("last_query", ""),
    ]);
    setEntries(list);
    setQuery(last);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onQueryChange = (value: string) => {
    setQuery(value);
    if (saveTimer.current !== null) {
      window.clearTimeout(saveTimer.current);
    }
    saveTimer.current = window.setTimeout(() => {
      setSetting("last_query", value);
    }, 300);
  };

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return entries;
    return entries.filter(
      (e) =>
        e.name.toLowerCase().includes(q) ||
        e.user.toLowerCase().includes(q)
    );
  }, [entries, query]);

  const onLock = async () => {
    setBusy(true);
    await lock();
    setBusy(false);
    onLocked();
  };

  const onSync = async () => {
    setBusy(true);
    const result = await sync();
    setBusy(false);
    toaster.toast({
      title: "DeckWarden",
      body: result.ok ? "Synced" : "Sync failed",
    });
    if (result.ok) await load();
  };

  const onReveal = (id: string, secret: string | null) => {
    setRevealed((prev) => {
      const next = { ...prev };
      if (secret === null) delete next[id];
      else next[id] = secret;
      return next;
    });
  };

  return (
    <>
      <PanelSection title="Vault">
        <PanelSectionRow>
          <TextField
            label="Search"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem layout="below" disabled={busy} onClick={onSync}>
            Sync
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem layout="below" disabled={busy} onClick={onLock}>
            Lock
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
      <PanelSection title={loading ? "Loading…" : `${filtered.length} entries`}>
        {filtered.map((entry) => (
          <PanelSectionRow key={entry.id}>
            <EntryRow
              entry={entry}
              revealed={revealed[entry.id] ?? null}
              onReveal={onReveal}
            />
          </PanelSectionRow>
        ))}
      </PanelSection>
    </>
  );
}

function Content() {
  const [st, setSt] = useState<Status | null>(null);

  const refresh = useCallback(async () => {
    setSt(await status());
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (st === null) {
    return (
      <PanelSection title="DeckWarden">
        <PanelSectionRow>
          <div>Checking vault…</div>
        </PanelSectionRow>
      </PanelSection>
    );
  }

  if (st.state === "missing") {
    return (
      <PanelSection title="Setup">
        <PanelSectionRow>
          <div>{st.error || "Bitwarden CLI (bw) not found"}</div>
        </PanelSectionRow>
        <PanelSectionRow>
          <div>Install bw into ~/.local/bin, then reopen.</div>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={refresh}>
            Retry
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
    );
  }

  if (st.state === "unlocked") {
    return (
      <SearchView
        onLocked={async () => {
          setSt({ ...st, state: "locked" });
        }}
      />
    );
  }

  if (st.state === "locked") {
    return (
      <UnlockView
        email={st.email}
        onUnlocked={() => setSt({ ...st, state: "unlocked" })}
        onLogout={async () => {
          await logout();
          await refresh();
        }}
      />
    );
  }

  return (
    <LoginView
      initialEmail={st.email}
      onUnlocked={() => setSt({ ...st, state: "unlocked" })}
    />
  );
}

export default definePlugin(() => {
  return {
    name: "DeckWarden",
    titleView: <div className={staticClasses.Title}>DeckWarden</div>,
    content: <Content />,
    icon: <FaKey />,
    onDismount() {},
  };
});
