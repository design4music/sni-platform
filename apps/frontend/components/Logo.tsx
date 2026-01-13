import Link from 'next/link';

export default function Logo() {
  return (
    <Link href="/" className="flex items-center gap-3">
      <div className="text-2xl font-bold tracking-tight">
        <span className="text-blue-500">WORLD</span>
        <span className="text-white">BRIEF</span>
      </div>
      <div className="hidden md:block text-sm text-gray-400" style={{ marginLeft: '0.75rem' }}>
        Understand the world. Briefly.
      </div>
    </Link>
  );
}
