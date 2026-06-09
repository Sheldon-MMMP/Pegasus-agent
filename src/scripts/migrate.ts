import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import { pool } from "../infrastructure/database.js";

const migrationsDirectory = path.join(process.cwd(), "migrations");
const migrations = (
  await readdir(migrationsDirectory, { withFileTypes: true })
)
  .filter((entry) => entry.isFile() && entry.name.endsWith(".sql"))
  .map((entry) => entry.name)
  .sort();

const client = await pool.connect();

try {
  await client.query(`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      filename text PRIMARY KEY,
      applied_at timestamptz NOT NULL DEFAULT now()
    )
  `);

  for (const filename of migrations) {
    const applied = await client.query(
      "SELECT 1 FROM schema_migrations WHERE filename = $1",
      [filename],
    );
    if (applied.rowCount) {
      console.log(`Skipping migration ${filename}.`);
      continue;
    }

    const sql = await readFile(path.join(migrationsDirectory, filename), "utf8");
    await client.query("BEGIN");
    try {
      await client.query(sql);
      await client.query(
        "INSERT INTO schema_migrations (filename) VALUES ($1)",
        [filename],
      );
      await client.query("COMMIT");
      console.log(`Applied migration ${filename}.`);
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    }
  }
} finally {
  client.release();
  await pool.end();
}

console.log("Database migration completed.");
