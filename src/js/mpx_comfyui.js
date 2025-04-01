import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
  name: "cg.custom.mpx_comfyui",
  init() {
    console.log("MPXComfyUI extension initialized");
  },
  setup() {
    let firstTimeLoadApiKeys = false;
    let firstTimeLoadDocs = false;

    // Test the API key on startup after 10 seconds
    setTimeout(() => {
      testAPIKeyOnStartup();
    }, 5000);

    setInterval(() => {
      testAPIKeyOnStartup();
    }, 10 * 60000); // Test the API key every 10 minutes

    const debounce = (func, delay) => {
      let timer;
      return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => func(...args), delay);
      };
    };

    const debouncedSaveAPIKeyToEnv = debounce(saveAPIKeyToEnv, 1000);

    app.ui.settings.addSetting({
      id: "MPX Settings.MPX",
      name: "API Key (Requires RESTART):",
      type: "text",
      onChange: (newValue) => {
        if (!firstTimeLoadApiKeys) {
          firstTimeLoadApiKeys = true;
          return;
        }
        debouncedSaveAPIKeyToEnv(newValue);
      },
    });

    app.ui.settings.addSetting({
      id: "MPX Settings.MPX Docs",
      name: "List of MPX Docs:",
      type: "combo",
      options: [
        {
          text: "MPX Getting Started",
          value: "https://docs.masterpiecex.com/docs/getting-started/",
        },
        {
          text: "MPX SDK Setup",
          value: "https://docs.masterpiecex.com/docs/masterpiece-x-sdk-setup/",
        },
      ],
      onChange: (newValue) => {
        if (!firstTimeLoadDocs) {
          firstTimeLoadDocs = true;
          return;
        }
        window.open(newValue, "_blank");
      },
    });
  },
});

async function testAPIKeyOnStartup() {
  console.log("Validating API key on startup...");
  const res = await api.fetchApi("/mpx_comfyui_api_key_test");
  const resData = await res.json();
  if (resData.status === "error") {
    window["app"].extensionManager.toast.add({
      severity: resData.status || "info",
      summary: "MPX",
      detail: resData.message || "Please restart ComfyUI.",
      life: 500e3,
    });
  }
}

async function saveAPIKeyToEnv(secretKey) {
  if (!secretKey) {
    return;
  }

  try {
    window["app"].extensionManager.toast.add({
      severity: "info",
      summary: "MPX",
      detail: "Validating the API key...",
      life: 2e3,
    });
    const body = new FormData();
    body.append("api_key", secretKey);
    const res = await api.fetchApi("/mpx_comfyui_api_key", {
      method: "POST",
      body,
    });
    const resData = await res.json();
    window["app"].extensionManager.toast.add({
      severity: resData.status || "info",
      summary: "MPX",
      detail: resData.message || "Please enter the API key.",
      life: 5e3,
    });
    app.ui.settings.setSettingValue("MPX Settings.MPX", "");
  } catch (error) {
    console.error(`Error: ${error}`);
    window["app"].extensionManager.toast.addAlert("Error: " + error);
  }
}
