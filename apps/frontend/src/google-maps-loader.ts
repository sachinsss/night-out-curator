const SCRIPT_SELECTOR = "script[data-nightline-google-maps]";
const CALLBACK_NAME = "__nightlineGoogleMapsReady";
let loadingPromise: Promise<typeof google> | null = null;
const authFailureListeners = new Set<(error: GoogleMapsLoadError) => void>();
let pendingReject: ((error: GoogleMapsLoadError) => void) | null = null;

export class GoogleMapsLoadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "GoogleMapsLoadError";
  }
}

export function onGoogleMapsAuthFailure(listener: (error: GoogleMapsLoadError) => void) {
  authFailureListeners.add(listener);
  return () => authFailureListeners.delete(listener);
}

export function loadGoogleMaps(apiKey: string): Promise<typeof google> {
  if (!apiKey.trim()) {
    return Promise.reject(
      new GoogleMapsLoadError(
        "Google Maps is not configured. Add VITE_GOOGLE_MAPS_API_KEY and restart the frontend.",
      ),
    );
  }
  if (window.google?.maps?.Map) return Promise.resolve(window.google);
  if (loadingPromise) return loadingPromise;

  loadingPromise = new Promise<typeof google>((resolve, reject) => {
    const callbackWindow = window as unknown as Window & Record<string, unknown>;
    pendingReject = reject;
    callbackWindow.gm_authFailure = () => {
      const error = new GoogleMapsLoadError(
        "Google Maps authentication failed. Check the browser key, Maps JavaScript API, and HTTP referrer restrictions.",
      );
      pendingReject?.(error);
      pendingReject = null;
      document.querySelector<HTMLScriptElement>(SCRIPT_SELECTOR)?.remove();
      loadingPromise = null;
      authFailureListeners.forEach((listener) => listener(error));
    };
    const finish = () => {
      delete callbackWindow[CALLBACK_NAME];
      if (window.google?.maps?.Map) {
        pendingReject = null;
        resolve(window.google);
      } else
        reject(
          new GoogleMapsLoadError("Google Maps loaded without the required Maps JavaScript API."),
        );
    };
    callbackWindow[CALLBACK_NAME] = finish;

    const existing = document.querySelector<HTMLScriptElement>(SCRIPT_SELECTOR);
    if (existing) return;

    const script = document.createElement("script");
    script.dataset.nightlineGoogleMaps = "true";
    script.async = true;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey.trim())}&callback=${CALLBACK_NAME}&loading=async&libraries=marker`;
    script.onerror = () => {
      delete callbackWindow[CALLBACK_NAME];
      pendingReject = null;
      script.remove();
      loadingPromise = null;
      reject(
        new GoogleMapsLoadError(
          "Google Maps could not be loaded. Check the browser key, API restrictions, and network connection.",
        ),
      );
    };
    document.head.append(script);
  }).catch((error) => {
    loadingPromise = null;
    throw error;
  });

  return loadingPromise;
}
