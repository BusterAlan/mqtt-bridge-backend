const mqtt = require("mqtt");
const EventEmitter = require("events");
const { mqtt: mqttConfig, topics } = require("../config/mqttConfig");

class MqttBridge extends EventEmitter {}

const mqttBridge = new MqttBridge();

// Build connection URL
const url = `${mqttConfig.host}:${mqttConfig.port}`;

// Connect to MQTT broker
const client = mqtt.connect(url, {
  username: mqttConfig.username,
  password: mqttConfig.password,
});

// Connection events
client.on("connect", () => {
  console.log("MQTT conectado al broker.");

  // Subscribe to topics
  client.subscribe([topics.state, topics.status], (err) => {
    if (err) {
      console.error("Error al suscribir topics:", err);
    } else {
      console.log("Suscrito a topics:", topics.state, topics.status);
    }
  });
});

// Error handling
client.on("error", (err) => {
  console.error("Error en MQTT:", err);
});

// Receive message from broker
client.on("message", (topic, msg) => {
  const payload = msg.toString();

  // Emitimos el evento para que el websocket lo pueda usar
  mqttBridge.emit("mqtt_message", { topic, payload });
});

// Publish function
function publish(topic, payload) {
  client.publish(topic, payload, { qos: 0 }, (err) => {
    if (err) {
      console.error("Error al publicar:", err);
    }
  });
}

module.exports = { mqttBridge, publish };
