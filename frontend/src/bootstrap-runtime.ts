const RUNTIME_CONFIG_SRC = '/runtime-config.js';
const RUNTIME_CONFIG_TIMEOUT_MS = 3000;

const resolveRuntimeConfig = (
  win: Window & typeof globalThis,
  doc: Document,
  timeoutMs: number,
): Promise<void> =>
  new Promise((resolve) => {
    win.__APP_CONFIG__ = win.__APP_CONFIG__ ?? {};

    const script = doc.createElement('script');
    let settled = false;

    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      win.clearTimeout(timeoutId);
      script.onload = null;
      script.onerror = null;
      resolve();
    };

    script.src = RUNTIME_CONFIG_SRC;
    script.async = true;
    script.onload = finish;
    script.onerror = finish;

    const timeoutId = win.setTimeout(finish, timeoutMs);
    doc.head.appendChild(script);
  });

export const loadRuntimeConfig = async (
  win: Window & typeof globalThis = window,
  doc: Document = document,
  timeoutMs = RUNTIME_CONFIG_TIMEOUT_MS,
): Promise<void> => {
  await resolveRuntimeConfig(win, doc, timeoutMs);
};
