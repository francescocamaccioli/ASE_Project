'use client';

import { useEffect, useState } from 'react';
import GatchaCard from '../../components/GatchaCard';

export default function Collection() {
  const [gatchas, setGatchas] = useState([]);
  const [userCollection, setUserCollection] = useState([]);
  const [balance, setBalance] = useState(0);
  const [userID, setUserID] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;

      // Fetch all gatchas
      const resGatchas = await fetch('https://localhost:5001/gatcha/gatchas', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const gatchasData = await resGatchas.json();
      setGatchas(gatchasData);

      // Fetch user collection
      const resCollection = await fetch('https://localhost:5001/user/collection', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const collectionData = await resCollection.json();
      setUserCollection(collectionData);

      // Fetch user balance
      const resBalance = await fetch('https://localhost:5001/user/balance', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const balanceData = await resBalance.json();
      setBalance(balanceData.balance);

      // Fetch user info
      const resUserInfo = await fetch('https://localhost:5001/auth/userinfo', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const userInfoData = await resUserInfo.json();
      setUserID(userInfoData.userID);
    };

    fetchData();
  }, []);

  const handleIncreaseBalance = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    await fetch('https://localhost:5001/user/increase_balance', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ amount: 1000 }),
    });

    // Update balance
    const resBalance = await fetch('https://localhost:5001/user/balance', {
      headers: { Authorization: `Bearer ${token}` },
    });
    const balanceData = await resBalance.json();
    setBalance(balanceData.balance);
  };

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">Your Gatcha Collection</h1>
      <p>Your Balance: {balance}</p>
      <p>Your UserID: {userID}</p>
      <button
        className="px-4 py-2 my-4 text-white bg-green-500"
        onClick={handleIncreaseBalance}
      >
        Increase Balance by 1000
      </button>
      <h2 className="mt-8 text-xl font-bold">Gatchas You Own</h2>
      <div className="grid grid-cols-1 gap-4 mt-4 md:grid-cols-3">
        {gatchas
          .filter((g) => userCollection.some((uc) => uc.gatcha_id === g._id))
          .map((gatcha) => (
            <GatchaCard key={gatcha._id} gatcha={gatcha} owned />
          ))}
      </div>
      <h2 className="mt-8 text-xl font-bold">Gatchas You Don't Own Yet</h2>
      <div className="grid grid-cols-1 gap-4 mt-4 md:grid-cols-3">
        {gatchas
          .filter((g) => !userCollection.some((uc) => uc.gatcha_id === g._id))
          .map((gatcha) => (
            <GatchaCard key={gatcha._id} gatcha={gatcha} />
          ))}
      </div>
    </div>
  );
}