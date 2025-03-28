import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

app.registerExtension({
    name: "mpx_genai_nodes.show_string",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        console.log("beforeRegisterNodeDef");
        if (nodeType.comfyClass === "ShowString") {
            console.log("nodeType.comfyClass === ShowString");

            // Note: because of an undocumented function (or likely a bug), string inputs can't be created before a widget, so I had JS reverse the order.
            const onCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                console.log("onNodeCreated");
                
                // Create preview widget first
                this.showValueWidget = ComfyWidgets["STRING"](this, "preview", ["STRING", { multiline: true }], app).widget;
                this.showValueWidget.inputEl.readOnly = true;
                this.showValueWidget.inputEl.style.opacity = 0.6;
                
                // Call original onNodeCreated to create string_in input
                onCreated?.apply(this, arguments);
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

