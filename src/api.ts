import { callable } from "@decky/api";

export type VaultEntry = {
  id: string;
  name: string;
  user: string;
};

export type UnlockResult = {
  ok: boolean;
  error?: string;
};

export const unlocked = callable<[], boolean>("unlocked");
export const unlock = callable<[password: string], UnlockResult>("unlock");
export const lock = callable<[], { ok: boolean }>("lock");
export const sync = callable<[], { ok: boolean; error?: string }>("sync");
export const listEntries = callable<[], VaultEntry[]>("list_entries");
export const getPassword = callable<[entryId: string], string>("get_password");
export const getUsername = callable<[entryId: string], string>("get_username");
export const getSetting = callable<[key: string, defaultValue: string], string>("get_setting");
export const setSetting = callable<[key: string, value: string], void>("set_setting");
