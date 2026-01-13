import Link from 'next/link';

export default function Logo() {
  return (
    <Link href="/" className="text-2xl font-bold tracking-tight">
      <span className="text-blue-500">SNI</span>
      <span className="text-gray-300 ml-1 text-sm font-normal">Strategic Narrative Intelligence</span>
    </Link>
  );
}
