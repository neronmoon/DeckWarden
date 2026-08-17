import { callable } from "@decky/api";

export type VaultEntry = {
  id: string;
  name: string;
  user: string;
};

export type Status = {
  state: "missing" | "logged_out" | "locked" | "unlocked";
  email: string;
  error?: string;
};

export type OkResult = {
  ok: boolean;
  error?: string;
  needs2fa?: boolean;
};

export const status = callable<[], Status>("status");
export const login = callable<
  [email: string, password: string, totp?: string, method?: number],
  OkResult
>("login");
export const unlock = callable<[password: string], OkResult>("unlock");
export const lock = callable<[], { ok: boolean }>("lock");
export const logout = callable<[], { ok: boolean }>("logout");
export const sync = callable<[], OkResult>("sync");
export const listEntries = callable<[], VaultEntry[]>("list_entries");
export const getPassword = callable<[entryId: string], string>("get_password");
export const getUsername = callable<[entryId: string], string>("get_username");
export const getSetting = callable<[key: string, defaultValue: string], string>("get_setting");
export const setSetting = callable<[key: string, value: string], void>("set_setting");
