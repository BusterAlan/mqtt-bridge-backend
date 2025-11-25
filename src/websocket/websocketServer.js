const WebSocket = require("ws");
const { publish } = require("../mqtt/mqttClient");
const { topics } = require("../config/mqttConfig");

function createWebSocketServer(server, mqttBridge) {
  const wss = new WebSocket.Server({ server });

  wss.on("connection", (ws) => {
    console.log("Cliente React conectado via WebSocket");

    // Cuando React envía algo → publicar en MQTT
    ws.on("message", (data) => {
      try {
        const msg = JSON.parse(data);

        if (msg.type === "setConfig") {
          publish(topics.configSet, JSON.stringify(msg.payload));
        }

      } catch (e) {
        console.error("Mensaje WebSocket inválido:", e);
      }
    });

    ws.on("close", () => {
      console.log("Cliente WebSocket desconectado");
    });
  });

  // Cuando MQTT recibe un mensaje → mandar a React
  mqttBridge.on("mqtt_message", (data) => {
    const json = JSON.stringify({
      type: "mqtt",
      topic: data.topic,
      payload: data.payload,
    });

    // broadcast
    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(json);
      }
    });
  });

  return wss;
}

module.exports = { createWebSocketServer };
