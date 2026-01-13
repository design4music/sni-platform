import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function GET() {
  try {
    const result = await query('SELECT NOW() as time');
    return NextResponse.json({
      status: 'ok',
      database: 'connected',
      timestamp: result[0].time,
    });
  } catch (error: any) {
    return NextResponse.json(
      {
        status: 'error',
        database: 'disconnected',
        error: error.message,
      },
      { status: 500 }
    );
  }
}
