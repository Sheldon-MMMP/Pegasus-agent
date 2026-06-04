import { readFile } from "node:fs/promises";
import path from "node:path";
import { pool } from "../infrastructure/database.js";

const migration = await readFile(
  path.join(process.cwd(), "migrations", "001_initial.sql"),
  "utf8",
);

await pool.query(migration);
await pool.end();
console.log("Database migration completed.");
