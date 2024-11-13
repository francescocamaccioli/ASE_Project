// init-gatcha-data.js
db.createCollection('results');
db.results.insertMany([
    {
        "gatcha_id": 1,
        "name": "Common Warrior",
        "image": "common_warrior.png",
        "rarity": "comune"
    },
    {
        "gatcha_id": 2,
        "name": "Rare Archer",
        "image": "rare_archer.png",
        "rarity": "raro"
    },
    {
        "gatcha_id": 3,
        "name": "Epic Mage",
        "image": "epic_mage.png",
        "rarity": "epico"
    },
    {
        "gatcha_id": 4,
        "name": "Legendary Dragon",
        "image": "legendary_dragon.png",
        "rarity": "leggendario"
    },
    {
        "gatcha_id": 5,
        "name": "Common Knight",
        "image": "common_knight.png",
        "rarity": "comune"
    },
    {
        "gatcha_id": 6,
        "name": "Rare Sorcerer",
        "image": "rare_sorcerer.png",
        "rarity": "raro"
    },
    {
        "gatcha_id": 7,
        "name": "Epic Beast",
        "image": "epic_beast.png",
        "rarity": "epico"
    },
    {
        "gatcha_id": 8,
        "name": "Legendary Phoenix",
        "image": "legendary_phoenix.png",
        "rarity": "leggendario"
    },
    {
        "gatcha_id": 9,
        "name": "Common Thief",
        "image": "common_thief.png",
        "rarity": "comune"
    },
    {
        "gatcha_id": 10,
        "name": "Rare Assassin",
        "image": "rare_assassin.png",
        "rarity": "raro"
    }
]);
console.log('Finished inserting data into results collection');
