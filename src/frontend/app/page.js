import Link from 'next/link';

export default function Home() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Welcome to the Gatcha Collection App</h1>
      <p>
        Please <Link href="/login" className="text-blue-500">Login</Link> or{' '}
        <Link href="/register" className="text-blue-500">Register</Link> to continue.
      </p>
    </div>
  );
}