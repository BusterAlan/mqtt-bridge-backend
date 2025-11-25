const express = require("express");
const http = require("http");
const { createWebSocketServer } = require("./websocket/websocketServer");
const { mqttBridge } = require("./mqtt/mqttClient");

function startServer() {
  const app = express();
  const server = http.createServer(app);

  // Crear servidor WS con Express
  createWebSocketServer(server, mqttBridge);

  const PORT = process.env.PORT || 3000;
  server.listen(PORT, () => {
    console.log(`Servidor corriendo en http://localhost:${PORT}`);
  });
}

module.exports = { startServer };
