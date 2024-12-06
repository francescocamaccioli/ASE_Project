'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const router = useRouter();

  const handleRegister = async (e) => {
    e.preventDefault();
    const res = await fetch('https://localhost:5001/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, email }),
    });

    if (res.ok) {
      router.push('/login');
    } else {
      alert('Registration failed');
    }
  };

  return (
    <form onSubmit={handleRegister} className="max-w-md mx-auto mt-8">
      <h1 className="mb-4 text-xl font-bold">Register</h1>
      <input
        type="text"
        placeholder="Username"
        className="w-full p-2 mb-4 border"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        type="email"
        placeholder="Email"
        className="w-full p-2 mb-4 border"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        className="w-full p-2 mb-4 border"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button className="px-4 py-2 text-white bg-blue-500" type="submit">
        Register
      </button>
    </form>
  );
}