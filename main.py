import asyncio
import os
import pwd
import shutil
import decky
from settings import SettingsManager
from list_parse import parse_list_line


class Plugin:
    async def _main(self):
        self.settings = SettingsManager(
            name="settings",
            settings_directory=decky.DECKY_PLUGIN_SETTINGS_DIR,
        )
        self.settings.read()
        self._pinentry_ready = False

    async def _unload(self):
        pass

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
        if extra:
            env.update(extra)
        return env

    def _rbw_path(self) -> str:
        configured = self.settings.getSetting("rbw_path", "")
        if configured and os.path.isfile(configured) and os.access(configured, os.X_OK):
            return configured
        home = self._home()
        for candidate in (
            os.path.join(home, ".local", "bin", "rbw"),
            os.path.join(home, ".cargo", "bin", "rbw"),
            "/usr/bin/rbw",
            "/usr/local/bin/rbw",
        ):
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        found = shutil.which("rbw")
        if found:
            return found
        raise FileNotFoundError("rbw not found")

    def _pinentry_path(self) -> str:
        return os.path.join(decky.DECKY_PLUGIN_DIR, "bin", "pinentry-deckwarden")

    async def _run(
        self,
        args: list[str],
        *,
        extra_env: dict[str, str] | None = None,
        input_text: str | None = None,
    ) -> tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if input_text is not None else None,
            env=self._env(extra_env),
        )
        stdout_b, stderr_b = await proc.communicate(
            input_text.encode() if input_text is not None else None
        )
        return proc.returncode or 0, stdout_b.decode(), stderr_b.decode()

    async def _ensure_pinentry(self) -> None:
        if self._pinentry_ready:
            return
        shim = self._pinentry_path()
        if not os.path.isfile(shim):
            raise FileNotFoundError(f"pinentry shim missing: {shim}")
        os.chmod(shim, 0o755)
        rbw = self._rbw_path()
        code, _, _ = await self._run([rbw, "config", "set", "pinentry", shim])
        if code != 0:
            raise RuntimeError("failed to set rbw pinentry")
        self._pinentry_ready = True

    async def unlocked(self) -> bool:
        try:
            rbw = self._rbw_path()
        except FileNotFoundError:
            return False
        code, _, _ = await self._run([rbw, "unlocked"])
        return code == 0

    async def unlock(self, password: str) -> dict:
        try:
            rbw = self._rbw_path()
        except FileNotFoundError as e:
            return {"ok": False, "error": str(e)}
        try:
            await self._ensure_pinentry()
        except Exception as e:
            return {"ok": False, "error": str(e)}

        runtime = self._runtime_dir()
        pin_dir = os.path.join(runtime, "deckwarden")
        pin_path = os.path.join(pin_dir, "pin")
        os.makedirs(pin_dir, mode=0o700, exist_ok=True)
        try:
            fd = os.open(pin_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(password)
            await self._run([rbw, "stop-agent"])
            code, _, _ = await self._run(
                [rbw, "unlock"],
                extra_env={"RBW_PIN": password},
            )
            if code != 0:
                return {"ok": False, "error": "unlock failed"}
            return {"ok": True}
        finally:
            try:
                os.unlink(pin_path)
            except FileNotFoundError:
                pass
            del password

    async def lock(self) -> dict:
        rbw = self._rbw_path()
        code, _, _ = await self._run([rbw, "lock"])
        return {"ok": code == 0}

    async def sync(self) -> dict:
        rbw = self._rbw_path()
        code, _, _ = await self._run([rbw, "sync"])
        return {"ok": code == 0, "error": "" if code == 0 else "sync failed"}

    async def list_entries(self) -> list[dict[str, str]]:
        rbw = self._rbw_path()
        code, stdout, _ = await self._run(
            [rbw, "list", "--fields", "id,name,user"]
        )
        if code != 0:
            return []
        entries = []
        for line in stdout.splitlines():
            if not line.strip():
                continue
            parsed = parse_list_line(line)
            if parsed:
                entries.append(parsed)
        return entries

    async def get_password(self, entry_id: str) -> str:
        rbw = self._rbw_path()
        code, stdout, _ = await self._run([rbw, "get", "--", entry_id])
        if code != 0:
            return ""
        return stdout.rstrip("\n")

    async def get_username(self, entry_id: str) -> str:
        rbw = self._rbw_path()
        code, stdout, _ = await self._run(
            [rbw, "get", "--field", "user", "--", entry_id]
        )
        if code != 0:
            return ""
        return stdout.rstrip("\n")

    async def get_setting(self, key: str, default: str = "") -> str:
        return self.settings.getSetting(key, default)

    async def set_setting(self, key: str, value: str) -> None:
        if key not in ("rbw_path", "last_query"):
            return
        self.settings.setSetting(key, value)
        self.settings.commit()
