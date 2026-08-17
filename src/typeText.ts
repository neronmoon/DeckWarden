import { Router, sleep } from "@decky/ui";
import type { SteamClient } from "@decky/ui/dist/globals/steam-client";

declare const SteamClient: SteamClient;

export async function typeText(text: string): Promise<void> {
  Router.CloseSideMenus();
  await sleep(500);
  for (const char of text) {
    SteamClient.Input.ControllerKeyboardSendText(char);
    await sleep(5);
  }
}
