const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const path = require("path");

const PORT = Number(process.env.PORT || 3000);
const ROOT = __dirname;
const rooms = new Map();
const users = new Map();

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
};

function sendFrame(socket, payload) {
  const data = Buffer.from(JSON.stringify(payload));
  let header;
  if (data.length < 126) {
    header = Buffer.from([0x81, data.length]);
  } else {
    header = Buffer.alloc(4);
    header[0] = 0x81;
    header[1] = 126;
    header.writeUInt16BE(data.length, 2);
  }
  socket.write(Buffer.concat([header, data]));
}

function readFrame(buffer) {
  const length = buffer[1] & 0x7f;
  let offset = 2;
  let payloadLength = length;
  if (length === 126) {
    payloadLength = buffer.readUInt16BE(offset);
    offset += 2;
  }
  const mask = buffer.subarray(offset, offset + 4);
  offset += 4;
  const payload = buffer.subarray(offset, offset + payloadLength);
  for (let index = 0; index < payload.length; index += 1) {
    payload[index] ^= mask[index % 4];
  }
  return JSON.parse(payload.toString("utf8"));
}

function clients(room) {
  if (!rooms.has(room)) rooms.set(room, new Set());
  return rooms.get(room);
}

function broadcast(room, payload, except = null) {
  clients(room).forEach((client) => {
    if (client !== except) sendFrame(client, payload);
  });
}

function serveStatic(request, response) {
  const urlPath = request.url === "/" ? "/index.html" : request.url;
  const filePath = path.normalize(path.join(ROOT, urlPath));
  if (!filePath.startsWith(ROOT)) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }
  fs.readFile(filePath, (error, data) => {
    if (error) {
      response.writeHead(404);
      response.end("Not found");
      return;
    }
    response.writeHead(200, { "Content-Type": mimeTypes[path.extname(filePath)] || "application/octet-stream" });
    response.end(data);
  });
}

const server = http.createServer(serveStatic);

server.on("upgrade", (request, socket) => {
  const key = request.headers["sec-websocket-key"];
  const accept = crypto.createHash("sha1")
    .update(`${key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11`)
    .digest("base64");

  socket.write([
    "HTTP/1.1 101 Switching Protocols",
    "Upgrade: websocket",
    "Connection: Upgrade",
    `Sec-WebSocket-Accept: ${accept}`,
    "",
    "",
  ].join("\r\n"));

  socket.on("data", (buffer) => {
    let message;
    try {
      message = readFrame(buffer);
    } catch {
      return;
    }

    if (message.type === "join") {
      socket.room = message.room;
      socket.playerName = message.name || "Joueur";
      users.set(socket.playerName, socket);
      const roomClients = clients(socket.room);
      roomClients.add(socket);
      const color = roomClients.size === 1 ? "white" : "black";
      sendFrame(socket, { type: "joined", room: socket.room, color });
      broadcast(socket.room, { type: "system", text: `${socket.playerName} a rejoint le salon.` }, socket);
      return;
    }

    if (!socket.room) return;
    if (message.type === "move") broadcast(socket.room, message, socket);
    if (message.type === "chat") broadcast(socket.room, message);
    if (message.type === "invite") {
      const target = users.get(message.to);
      if (target) {
        sendFrame(target, { type: "invite", from: message.from, room: message.room });
      } else {
        sendFrame(socket, { type: "system", text: `${message.to} n'est pas connecte.` });
      }
    }
    if (message.type === "private") {
      const target = users.get(message.to);
      if (target) {
        sendFrame(target, { type: "private", from: message.from, text: message.text });
      } else {
        sendFrame(socket, { type: "system", text: `${message.to} n'est pas connecte pour recevoir le message prive.` });
      }
    }
  });

  socket.on("close", () => {
    if (!socket.room) return;
    clients(socket.room).delete(socket);
    if (socket.playerName) users.delete(socket.playerName);
    broadcast(socket.room, { type: "system", text: `${socket.playerName || "Un joueur"} a quitte le salon.` });
  });
});

server.listen(PORT, () => {
  console.log(`Chess AI web server running on http://localhost:${PORT}`);
});
