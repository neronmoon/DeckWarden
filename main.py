import asyncio
import json
import os
import pwd
import shutil

import decky
from settings import SettingsManager
from item_parse import entries_from_items

LOGIN_TIMEOUT = 120
DEFAULT_TIMEOUT = 60


def _err_tail(stderr: str, stdout: str = "") -> str:
    text = (stderr or stdout or "").strip()
    if not text:
        return "unknown error"
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return lines[-1][:200] if lines else "unknown error"


class Plugin:
    async def _main(self):
        self.settings = SettingsManager(
            name="settings",
            settings_directory=decky.DECKY_PLUGIN_SETTINGS_DIR,
        )
        self.settings.read()
        self._session: str | None = None
        decky.logger.info("DeckWarden loaded log=%s", decky.DECKY_PLUGIN_LOG)

    async def _unload(self):
        self._session = None

    def _home(self) -> str:
        return decky.DECKY_USER_HOME

    def _runtime_dir(self) -> str:
        try:
            uid = pwd.getpwnam(os.path.basename(self._home())).pw_uid
        except KeyError:
            uid = os.getuid()
        return f"/run/user/{uid}"

    def _env(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = self._home()
        env["XDG_RUNTIME_DIR"] = self._runtime_dir()
        if self._session:
            env["BW_SESSION"] = self._session
        if extra:
            env.update(extra)
        return env

    def _bundled_bw(self) -> str:
        return os.path.join(decky.DECKY_PLUGIN_DIR, "bin", "bw")

    def _bw_path(self) -> str:
        configured = self.settings.getSetting("bw_path", "")
        if configured and os.path.isfile(configured) and os.access(configured, os.X_OK):
            return configured
        bundled = self._bundled_bw()
        if os.path.isfile(bundled):
            os.chmod(bundled, 0o755)
            return bundled
        home = self._home()
        for candidate in (
            os.path.join(home, ".local", "bin", "bw"),
            os.path.join(home, "bin", "bw"),
            "/usr/bin/bw",
            "/usr/local/bin/bw",
        ):
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        found = shutil.which("bw")
        if found:
            return found
        raise FileNotFoundError("bw not found — rebuild plugin to bundle CLI")

    async def _run(
        self,
        args: list[str],
        *,
        extra_env: dict[str, str] | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> tuple[int, str, str]:
        label = " ".join(args[1:3] if len(args) > 1 else args)
        decky.logger.info("bw run: %s", label)
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
            env=self._env(extra_env),
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            decky.logger.error("bw timeout after %ss: %s", timeout, label)
            return 124, "", f"timeout after {int(timeout)}s"
        code = proc.returncode or 0
        stdout = stdout_b.decode(errors="replace")
        stderr = stderr_b.decode(errors="replace")
        if code != 0:
            decky.logger.error(
                "bw failed code=%s cmd=%s err=%s",
                code,
                label,
                _err_tail(stderr, stdout),
            )
        else:
            decky.logger.info("bw ok: %s", label)
        return code, stdout, stderr

    async def _bw_status(self) -> dict:
        bw = self._bw_path()
        code, stdout, _ = await self._run(
            [bw, "status", "--raw", "--nointeraction"], timeout=30
        )
        if code != 0 or not stdout.strip():
            return {"status": "unauthenticated", "userEmail": ""}
        return json.loads(stdout)

    async def status(self) -> dict:
        try:
            raw = await self._bw_status()
        except FileNotFoundError as e:
            return {
                "state": "missing",
                "email": "",
                "error": str(e),
            }
        email = raw.get("userEmail") or self.settings.getSetting("email", "")
        st = raw.get("status", "unauthenticated")
        if self._session and st == "unlocked":
            state = "unlocked"
        elif st == "unlocked" and not self._session:
            state = "locked"
        elif st == "locked":
            state = "locked"
        elif st == "unauthenticated":
            state = "logged_out"
        else:
            state = "locked" if email else "logged_out"
        if state != "unlocked":
            self._session = None
        return {"state": state, "email": email}

    async def login(self, email: str, password: str) -> dict:
        try:
            bw = self._bw_path()
        except FileNotFoundError as e:
            return {"ok": False, "error": str(e)}
        email = email.strip()
        if not email or not password:
            return {"ok": False, "error": "email and password required"}
        self.settings.setSetting("email", email)
        self.settings.commit()
        decky.logger.info("login start email=%s bw=%s", email, bw)
        try:
            code, stdout, stderr = await self._run(
                [
                    bw,
                    "login",
                    email,
                    "--passwordenv",
                    "BW_PASSWORD",
                    "--raw",
                    "--nointeraction",
                ],
                extra_env={"BW_PASSWORD": password},
                timeout=LOGIN_TIMEOUT,
            )
            combined = (stderr + stdout).lower()
            if code != 0:
                if "already logged in" in combined:
                    decky.logger.info("already logged in, unlocking")
                    return await self.unlock(password)
                return {"ok": False, "error": _err_tail(stderr, stdout)}
            session = stdout.strip()
            if not session:
                return {"ok": False, "error": "no session from login"}
            self._session = session
            decky.logger.info("login ok, syncing")
            sync_code, _, sync_err = await self._run(
                [bw, "sync", "--nointeraction"], timeout=LOGIN_TIMEOUT
            )
            if sync_code != 0:
                decky.logger.error("sync after login failed: %s", _err_tail(sync_err))
            return {"ok": True}
        finally:
            del password

    async def unlock(self, password: str) -> dict:
        try:
            bw = self._bw_path()
        except FileNotFoundError as e:
            return {"ok": False, "error": str(e)}
        if not password:
            return {"ok": False, "error": "password required"}
        decky.logger.info("unlock start")
        try:
            raw = await self._bw_status()
            if raw.get("status") == "unauthenticated":
                email = self.settings.getSetting("email", "")
                if not email:
                    return {"ok": False, "error": "login first"}
                return await self.login(email, password)
            code, stdout, stderr = await self._run(
                [
                    bw,
                    "unlock",
                    "--passwordenv",
                    "BW_PASSWORD",
                    "--raw",
                    "--nointeraction",
                ],
                extra_env={"BW_PASSWORD": password},
                timeout=LOGIN_TIMEOUT,
            )
            if code != 0:
                return {"ok": False, "error": _err_tail(stderr, stdout)}
            session = stdout.strip()
            if not session:
                return {"ok": False, "error": "no session from unlock"}
            self._session = session
            decky.logger.info("unlock ok")
            return {"ok": True}
        finally:
            del password

    async def lock(self) -> dict:
        self._session = None
        try:
            bw = self._bw_path()
            await self._run([bw, "lock", "--nointeraction"], timeout=30)
        except FileNotFoundError:
            pass
        return {"ok": True}

    async def logout(self) -> dict:
        self._session = None
        try:
            bw = self._bw_path()
            await self._run([bw, "logout", "--nointeraction"], timeout=30)
        except FileNotFoundError:
            pass
        return {"ok": True}

    async def sync(self) -> dict:
        if not self._session:
            return {"ok": False, "error": "locked"}
        bw = self._bw_path()
        code, _, stderr = await self._run(
            [bw, "sync", "--nointeraction"], timeout=LOGIN_TIMEOUT
        )
        return {
            "ok": code == 0,
            "error": "" if code == 0 else _err_tail(stderr),
        }

    async def list_entries(self) -> list[dict[str, str]]:
        if not self._session:
            return []
        bw = self._bw_path()
        code, stdout, _ = await self._run(
            [bw, "list", "items", "--nointeraction"], timeout=DEFAULT_TIMEOUT
        )
        if code != 0 or not stdout.strip():
            return []
        return entries_from_items(json.loads(stdout))

    async def get_password(self, entry_id: str) -> str:
        if not self._session:
            return ""
        bw = self._bw_path()
        code, stdout, _ = await self._run(
            [bw, "get", "password", entry_id, "--nointeraction"], timeout=30
        )
        if code != 0:
            return ""
        return stdout.rstrip("\n")

    async def get_username(self, entry_id: str) -> str:
        if not self._session:
            return ""
        bw = self._bw_path()
        code, stdout, _ = await self._run(
            [bw, "get", "username", entry_id, "--nointeraction"], timeout=30
        )
        if code != 0:
            return ""
        return stdout.rstrip("\n")

    async def get_setting(self, key: str, default: str = "") -> str:
        return self.settings.getSetting(key, default)

    async def set_setting(self, key: str, value: str) -> None:
        if key not in ("bw_path", "last_query", "email"):
            return
        self.settings.setSetting(key, value)
        self.settings.commit()
