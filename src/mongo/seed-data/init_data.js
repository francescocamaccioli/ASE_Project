// init-gatcha-data.js
db.createCollection('gatchas');
db.gatchas.insertMany([
    {
        "_id": 1,
        "name": "Common Warrior",
        "image": "common_warrior.png",
        "rarity": "comune",
        "NTot": 0
    },
    {
        "_id": 2,
        "name": "Rare Archer",
        "image": "rare_archer.png",
        "rarity": "raro",
        "NTot": 0
    },
    {
        "_id": 3,
        "name": "Epic Mage",
        "image": "epic_mage.png",
        "rarity": "epico",
        "NTot": 0
    },
    {
        "_id": 4,
        "name": "Legendary Dragon",
        "image": "legendary_dragon.png",
        "rarity": "leggendario",
        "NTot": 0
    },
    {
        "_id": 5,
        "name": "Common Knight",
        "image": "common_knight.png",
        "rarity": "comune",
        "NTot": 0
    },
    {
        "_id": 6,
        "name": "Rare Sorcerer",
        "image": "rare_sorcerer.png",
        "rarity": "raro",
        "NTot": 0
    },
    {
        "_id": 7,
        "name": "Epic Beast",
        "image": "epic_beast.png",
        "rarity": "epico",
        "NTot": 0
    },
    {
        "_id": 8,
        "name": "Legendary Phoenix",
        "image": "legendary_phoenix.png",
        "rarity": "leggendario",
        "NTot": 0
    },
    {
        "_id": 9,
        "name": "Common Thief",
        "image": "common_thief.png",
        "rarity": "comune",
        "NTot": 0
    },
    {
        "_id": 10,
        "name": "Rare Assassin",
        "image": "rare_assassin.png",
        "rarity": "raro",
        "NTot": 0
    }
]);
console.log('Finished inserting data into gatchas collection');