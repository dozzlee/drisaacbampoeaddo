const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const root = __dirname;
const dataDir = process.env.DATA_DIR || path.join(root, "data");
const uploadsDir = path.join(dataDir, "tribute-uploads");
const indexFile = path.join(dataDir, "tribute-files.json");
const port = Number(process.env.PORT || 3000);
const maxBodyBytes = 16 * 1024 * 1024;
const allowedTypes = new Set([
  "image/jpeg", "image/png", "image/webp", "image/gif",
  "application/pdf", "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]);

fs.mkdirSync(uploadsDir, { recursive: true });

function readIndex() {
  try { return JSON.parse(fs.readFileSync(indexFile, "utf8")); }
  catch { return {}; }
}

function writeIndex(value) {
  const temporary = `${indexFile}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(value, null, 2));
  fs.renameSync(temporary, indexFile);
}

function json(response, status, payload) {
  response.writeHead(status, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
  response.end(JSON.stringify(payload));
}

function mimeType(filename) {
  const extension = path.extname(filename).toLowerCase();
  return ({
    ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".gif": "image/gif", ".svg": "image/svg+xml",
    ".pdf": "application/pdf", ".ico": "image/x-icon"
  })[extension] || "application/octet-stream";
}

function safeName(filename) {
  const extension = path.extname(filename).toLowerCase().replace(/[^.a-z0-9]/g, "");
  const base = path.basename(filename, path.extname(filename)).replace(/[^a-zA-Z0-9_-]+/g, "-").slice(0, 60) || "file";
  return `${Date.now()}-${crypto.randomBytes(5).toString("hex")}-${base}${extension}`;
}

function receiveJson(request) {
  return new Promise((resolve, reject) => {
    let body = "";
    request.on("data", chunk => {
      body += chunk;
      if (Buffer.byteLength(body) > maxBodyBytes) request.destroy(new Error("File is too large"));
    });
    request.on("end", () => {
      try { resolve(JSON.parse(body)); }
      catch { reject(new Error("Invalid upload data")); }
    });
    request.on("error", reject);
  });
}

async function handleApi(request, response, pathname) {
  if (request.method === "GET" && pathname === "/api/tributes/files") {
    return json(response, 200, readIndex());
  }

  const uploadMatch = pathname.match(/^\/api\/tributes\/(\d+)\/files$/);
  if (request.method === "POST" && uploadMatch) {
    try {
      const body = await receiveJson(request);
      if (!body.name || !body.type || !body.data || !allowedTypes.has(body.type)) {
        return json(response, 400, { error: "Unsupported or incomplete file" });
      }
      const match = String(body.data).match(/^data:[^;]+;base64,(.+)$/);
      if (!match) return json(response, 400, { error: "Invalid file data" });
      const buffer = Buffer.from(match[1], "base64");
      if (!buffer.length || buffer.length > 10 * 1024 * 1024) {
        return json(response, 413, { error: "Files must be smaller than 10 MB" });
      }
      const storedName = safeName(body.name);
      fs.writeFileSync(path.join(uploadsDir, storedName), buffer);
      const record = {
        id: crypto.randomUUID(), name: path.basename(body.name),
        href: `/uploads/${storedName}`, size: buffer.length,
        uploadedAt: new Date().toISOString()
      };
      const index = readIndex();
      const partyId = uploadMatch[1];
      index[partyId] = [...(index[partyId] || []), record];
      writeIndex(index);
      return json(response, 201, record);
    } catch (error) {
      return json(response, 400, { error: error.message || "Upload failed" });
    }
  }

  return json(response, 404, { error: "Not found" });
}

function serveFile(response, filename) {
  fs.stat(filename, (error, stats) => {
    if (error || !stats.isFile()) {
      response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      return response.end("Not found");
    }
    response.writeHead(200, { "Content-Type": mimeType(filename), "Content-Length": stats.size });
    fs.createReadStream(filename).pipe(response);
  });
}

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url, `http://${request.headers.host || "localhost"}`);
  const pathname = decodeURIComponent(url.pathname);
  if (pathname.startsWith("/api/")) return handleApi(request, response, pathname);
  if (pathname.startsWith("/uploads/")) {
    const filename = path.resolve(uploadsDir, pathname.slice("/uploads/".length));
    if (!filename.startsWith(`${uploadsDir}${path.sep}`)) return json(response, 403, { error: "Forbidden" });
    return serveFile(response, filename);
  }
  let requested = pathname;
  if (requested === "/") requested = "/index.html";
  else if (requested.endsWith("/")) requested += "index.html";
  const filename = path.resolve(root, `.${requested}`);
  if (!filename.startsWith(`${root}${path.sep}`)) return json(response, 403, { error: "Forbidden" });
  serveFile(response, filename);
});

server.listen(port, "0.0.0.0", () => console.log(`Memorial site listening on port ${port}`));
