'use client';

export default function GatchaCard({ gatcha, owned }) {
  const imageUrl = `https://localhost:5001${gatcha.image}`;

  return (
    <div className="p-4 border">
      <img src={imageUrl} alt={gatcha.name} className="object-cover w-full h-48" />
      <h3 className="mt-2 text-lg font-bold">{gatcha.name}</h3>
      <p>Rarity: {gatcha.rarity}</p>
      {owned ? (
        <p className="text-green-500">You own this gatcha</p>
      ) : (
        <p className="text-red-500">You don't own this gatcha</p>
      )}
    </div>
  );
}