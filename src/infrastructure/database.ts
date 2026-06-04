import pg from "pg";

const { Pool } = pg;

export const pool = new Pool({
  connectionString:
    process.env.DATABASE_URL ?? "postgresql://agent:agent@localhost:5432/agent",
});

export async function withTransaction<T>(
  callback: (client: pg.PoolClient) => Promise<T>,
): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const value = await callback(client);
    await client.query("COMMIT");
    return value;
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}
