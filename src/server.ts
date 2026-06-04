import { pool } from "./infrastructure/database.js";
import { createApp } from "./interfaces/http/app.js";
import { syncSkills } from "./services/skill.service.js";

const port = Number(process.env.PORT ?? 8000);

await syncSkills();

const server = createApp().listen(port, () => {
  console.log(`Agent server listening on http://localhost:${port}`);
});

let shuttingDown = false;

async function shutdown(): Promise<void> {
  if (shuttingDown) return;
  shuttingDown = true;
  await new Promise<void>((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
  await pool.end();
}

process.on("SIGINT", () => void shutdown().then(() => process.exit(0)));
process.on("SIGTERM", () => void shutdown().then(() => process.exit(0)));
