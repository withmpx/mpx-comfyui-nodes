import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

app.registerExtension({
    name: "mpx_genai_nodes.show_list",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        console.log("beforeRegisterNodeDef");
        if (nodeType.comfyClass === "ShowList") {
            console.log("nodeType.comfyClass === ShowList");

            nodeType.prototype.onNodeCreated = function() {
                console.log("onNodeCreated");
                this.showValueWidget = ComfyWidgets["STRING"](this, "preview", ["STRING", { multiline: true }], app).widget;
                this.showValueWidget.inputEl.readOnly = true;
                this.showValueWidget.inputEl.style.opacity = 0.6;
            };

            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                console.log("onExecuted");
                console.log(`message: ${message}`);
                onExecuted?.apply(this, arguments);
                if (message?.list?.[0] !== undefined) {
                    this.showValueWidget.value = message.list[0];
                }
            };
        }
    }
});

