'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function Navbar() {
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  return (
    <nav className="flex justify-between p-4 text-white bg-gray-800">
      <div>
        <Link href="/collection" className="mr-4">Collection</Link>
      </div>
      <button onClick={handleLogout}>Logout</button>
    </nav>
  );
}