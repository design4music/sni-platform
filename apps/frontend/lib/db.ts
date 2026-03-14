import { Pool } from 'pg';

let pool: Pool | null = null;

export function getPool(): Pool {
  if (!pool) {
    const poolOpts = {
      max: 10,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 30000,
      statement_timeout: 30000,
    };
    if (process.env.DATABASE_URL) {
      pool = new Pool({
        connectionString: process.env.DATABASE_URL,
        ssl: { rejectUnauthorized: false },
        ...poolOpts,
      });
    } else {
      pool = new Pool({
        host: process.env.DB_HOST,
        port: parseInt(process.env.DB_PORT || '5432'),
        database: process.env.DB_NAME,
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        ...poolOpts,
      });
    }
  }
  return pool;
}

function isConnectionError(err: any): boolean {
  const msg = err?.message || '';
  return msg.includes('Connection terminated') || msg.includes('ECONNREFUSED')
    || msg.includes('ETIMEDOUT') || msg.includes('connection timeout');
}

export async function query<T = any>(text: string, params?: any[]): Promise<T[]> {
  const pool = getPool();
  try {
    const result = await pool.query(text, params);
    return result.rows;
  } catch (err) {
    if (isConnectionError(err)) {
      console.warn('[db] connection failed, returning empty:', (err as Error).message);
      return [];
    }
    throw err;
  }
}

export async function queryNoJIT<T = any>(text: string, params?: any[]): Promise<T[]> {
  const pool = getPool();
  try {
    const client = await pool.connect();
    try {
      await client.query('SET LOCAL jit = off');
      const result = await client.query(text, params);
      return result.rows;
    } finally {
      client.release();
    }
  } catch (err) {
    if (isConnectionError(err)) {
      console.warn('[db] connection failed, returning empty:', (err as Error).message);
      return [];
    }
    throw err;
  }
}
